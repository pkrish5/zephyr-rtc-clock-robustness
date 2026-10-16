# Phase 1 extension: independently clocked RTC alarm — 2026-09-28

## Scope

After the ten-suite HSI baseline produced no eligible flips, the user approved a separate RTC-clock pilot before agent generation. The [protocol](../subjects/phase1_lsi_rtc/PROTOCOL.md) fixed the test, board, legal frequency range, 30 seeds, endpoints, eligibility rule, and analysis before any varied-LSI run. This is a selected, upstream-maintained Zephyr test configuration and a mechanism check. It is not a representative sample of human tests, nor an agent comparison or repair result.

The STM32F4 Discovery board's RTC uses the LSI oscillator. [ST's STM32F407 datasheet, DS8626 Table 35](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) gives LSI 17–47 kHz (typical 32 kHz) at VDD 3 V over −40 to 105 °C. Zephyr's pinned [STM32 RTC driver](../subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c) programs prescalers for 32 kHz LSI. The [Renode RTC model](https://github.com/renode/renode-infrastructure/blob/master/src/Emulator/Peripherals/Peripherals/Timers/STM32F4_RTC.cs) exposes this clock as an independent constructor frequency, so the study changes it while holding CPU performance, SysTick frequency, firmware ELF, and test source fixed. These values are hardware-bounded inputs to a model; they are not measured clocks on a particular board.

## Subject and frozen configuration

Zephyr v4.3.0 commit `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056` supplies [`test_alarm_callback.c`](../subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c) and the suite declaration unchanged. The [study wrapper](../subjects/phase1_lsi_rtc/selected_alarm_callback/CMakeLists.txt) links these exact C files, enables optional RTC alarms, and chooses the supported seconds/minutes/hours mask (`7`). The board overlay adds the `rtc` alias and selects the same 16 MHz HSI CPU setup as Phase 1. This wrapper choice is disclosed because it is not the upstream test's default application build. The full upstream `rtc_api` application was also built and run at nominal LSI as a compatibility pilot; its ELF and denominator remain separate.

The selected test sets the RTC to 23:59:55 and an alarm at 00:00:05, verifies no premature callback after 3 CPU-clock seconds, then assumes the callback has occurred after another fixed 10 seconds. It repeats this sequence. At 17 kHz, the configured RTC prescalers imply about `10 × 32000 / 17000 = 18.82` CPU seconds for ten RTC seconds, so the fixed 13-second assertion has no support from this oscillator bound. The exact event time includes setup and interrupt dispatch and must be observed in the trace.

## Results and classification

The full upstream suite passed its nominal compatibility pilot: four pass, one skip. The selected case passed at nominal 32 kHz and the exact 47 kHz endpoint; it failed at the 17 kHz endpoint at the upstream assertion “Alarm 0 callback should have been called.” In a separate diagnostic continuation of the same frozen selected ELF at 17 kHz, the RTC time register read 00:00:02 with callback flag clear at 13.5 virtual seconds, then 00:00:05 with callback flag set at 20 seconds. At the highest failing seeded frequency, 24,428 Hz, the assertion fails around 13 seconds of test time, but the callback flag is already set by the 13.5-second diagnostic checkpoint. The [17 kHz](../results/phase1_lsi_alarm/late_alarm_probe.json) and [24,428 Hz](../results/phase1_lsi_alarm/late_alarm_probe_24428hz.json) diagnostics are outside the primary rate. They support late events in Renode rather than permanently missing callbacks.

| Registered condition | Outcome |
| --- | --- |
| Selected nominal, 32 kHz | 1 pass / 1 case |
| 30 seeded frequencies, uniform integers in 17–47 kHz | **7 fail, 23 pass, 0 unresolved** |
| Exact low endpoint, 17 kHz | 1 fail; analyzed separately |
| Exact high endpoint, 47 kHz | 1 pass; analyzed separately |

The selected upstream case flipped on **7/30 seeded schedules = 23.3%**, with a **95% Wilson interval of 11.8–40.9%** for the registered uniform-frequency sampling design. The seven failing frequencies were 20,500–24,428 Hz; the lowest passing sampled frequency was 24,734 Hz. The nominal-prescaler estimate places the fixed-wait boundary near 24,615 Hz, consistent with this observed separation. This interval describes random frequency draws for this *one fixed test and Renode model*; it is not an estimate of the fraction of brittle upstream tests. The exact endpoints are challenge cases and are excluded from 7/30.

The [analysis script](../analysis/phase1_lsi_rtc_summary.py) validated all 33 selected-case records against the frozen build, source/config, simulator version, frequency mapping, saved platform, UART, and trace; it found no missing or harness-error runs. All **eight failures** (seven seeded and the low endpoint) failed at the same upstream line 140 and had **identical sampled traces and verdicts on fresh-process replay**. The explicit [decision file](../analysis/phase1_lsi_rtc_classification_decisions.json) assigns all eight to **brittle test assumption in this simulation** using the fixed-wait calculation, line-level evidence, and two post-failure register/callback probes. The derived [classification table](../results/phase1_lsi_alarm/classifications.json) contains exactly one label per flip: seven seeded plus one endpoint brittle; zero firmware-bug, model-artifact, or unknown labels. The model-specific assignment still needs physical validation before a silicon claim.

## Reproduce

Follow the [Phase 1 host setup](../harness/phase1/SETUP.md) for Zephyr SDK 0.17.4, project-local Python/west/CMake, and Renode 1.17.0. Run from the repository root in a fresh workspace or with empty output directories. The scripts refuse to overwrite raw artifacts. `ZEPHYR_SDK_INSTALL_DIR` and `RENODE_BIN` should name the installed SDK and simulator on that host. These commands reproduce the full-suite compatibility pilot and the selected-case study.

```sh
export ZEPHYR_SDK_INSTALL_DIR=/private/tmp/phase1-zephyr-sdk
export RENODE_BIN=/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode
export ZEPHYR_BASE="$PWD/subjects/upstream/zephyr"
export PATH="$PWD/.venv/bin:$PATH"
mkdir -p results/phase1_lsi_alarm
mkdir -p results/phase1_lsi_rtc
west build -p always -b stm32f4_disco \
  subjects/upstream/zephyr/tests/drivers/rtc/rtc_api \
  -d subjects/phase1_lsi_rtc/build/rtc_api \
  -- "-DDTC_OVERLAY_FILE=$PWD/subjects/phase1_zephyr/config/stm32f4_hsi.overlay;$PWD/subjects/phase1_lsi_rtc/rtc_alias.overlay" \
  "-DEXTRA_CONF_FILE=$PWD/subjects/phase1_lsi_rtc/rtc_alarm.conf" \
  > results/phase1_lsi_rtc/build.log 2>&1
python3 harness/phase1_lsi_rtc/run.py --condition nominal --count 1 --max-virtual-sec 150
west build -p always -b stm32f4_disco \
  subjects/phase1_lsi_rtc/selected_alarm_callback \
  -d subjects/phase1_lsi_rtc/build/rtc_alarm_callback \
  -- "-DDTC_OVERLAY_FILE=$PWD/subjects/phase1_zephyr/config/stm32f4_hsi.overlay;$PWD/subjects/phase1_lsi_rtc/rtc_alias.overlay" \
  > results/phase1_lsi_alarm/build.log 2>&1
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/run.py --condition nominal --count 1 --max-virtual-sec 60
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/run.py --condition perturbed --start 0 --count 30 --max-virtual-sec 60
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/run.py --condition min --count 1 --max-virtual-sec 60
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/run.py --condition max --count 1 --max-virtual-sec 60
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/replay.py --all-failures
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/late_alarm_probe.py
PHASE1_LSI_VARIANT=callback python3 harness/phase1_lsi_rtc/late_alarm_probe.py --frequency-hz 24428
python3 analysis/phase1_lsi_rtc_summary.py
```

The immutable [build manifest](../results/phase1_lsi_alarm/build.json) records the ELF (`d1ff902e1ebbb9e92fa03a7ecc14d208fb72f3b41ef2cb833bc275588d3f715d`), upstream source, wrapper, overlay, and build-log hashes. [JSONL runs](../results/phase1_lsi_alarm/runs.jsonl) record seed, exact frequency, bound citation, Renode 1.17.0 version, platform hash, UART hash, sampled virtual-time trace hash, and verdict. Derived [summary](../results/phase1_lsi_alarm/summary.json) and [classifications](../results/phase1_lsi_alarm/classifications.json) are regenerated by the analysis script; the underlying raw files are not edited.

## Limits and next gate

The ST frequency span covers a temperature range and does not prove that any single room-temperature unit attains all sampled values. Its LSI range is characterized rather than production-tested at every point. Renode's RTC, interrupt routing, and timing are abstractions of silicon. We did not establish a second simulator or physical-board reproduction in this extension. This extension selects one test whose 13-second wait sits inside the documented LSI span, so it demonstrates **existence in a specified simulation configuration**, not a population flip rate. The earlier HSI 0/299 remains a separate negative result and cannot be directly contrasted as an agent-versus-human effect. No agent suites have been generated or repaired. **The RTC extension stops here for review before Phase 2.**

**Assessment:** the independent LSI setting is viable as a controlled RQ2 schedule arm: it produced replayable verdict flips without changing the test or firmware ELF, and register observations explain their direction. It is not yet an accurate *comparative baseline* by itself. A paper needs more upstream RTC/interrupt cases selected by a rule that does not depend on observed flips, matched agent suites for the same behavior, and at least a targeted physical or second-model check of the RTC timing path. Keep this 7/30 result as a transparent selected-case pilot.
