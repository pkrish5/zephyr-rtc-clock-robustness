# Phase 1 extension: independently clocked RTC alarm baseline

Registered 2026-09-28 **before any varied-LSI run**. The already completed full upstream `rtc_api` suite at nominal 32 kHz is a compatibility pilot (4 pass, 1 skip) and is kept under `results/phase1_lsi_rtc/`. It is not pooled with the earlier HSI baseline.

## Selected upstream case and eligibility

The selected test is Zephyr v4.3.0 `tests/drivers/rtc/rtc_api/src/test_alarm_callback.c`, with its unmodified `src/main.c` suite declaration. A study-owned CMake/prj wrapper links only these two upstream C files to keep a single interrupt-driven objective and make 30 runs tractable. The board is STM32F4 Discovery / STM32F407VG; a tracked overlay adds the RTC alias and selects the existing board LSI RTC path. The wrapper enables `CONFIG_RTC_ALARM` and uses supported alarm fields second, minute, and hour (mask 7). This configuration is fixed before nominal and varied runs. The selected ELF must pass nominally at 32,000 Hz to enter the flip denominator. Retain any nominal failure as an exclusion, with raw output.

## Prespecified schedule and hardware bound

The [STM32F407 datasheet, DS8626 Table 35](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf) specifies LSI frequency **17–47 kHz**, nominal 32 kHz, at VDD = 3 V over ambient −40 to 105 °C. This is a separate oscillator from the CPU HSI. Set Renode's RTC model `wakeupTimerFrequency` to an integer in this range while keeping the same ELF, 16 MHz SysTick model, 16 MIPS CPU setting, and 1 µs quantum. The [Renode RTC model source](https://github.com/renode/renode-infrastructure/blob/master/src/Emulator/Peripherals/Peripherals/Timers/STM32F4_RTC.cs) shows that this constructor frequency drives its RTC timers. Nominal is 32,000 Hz; exact 17,000 and 47,000 Hz endpoints are challenge schedules reported separately. The primary sample is seeds **0–29**, mapped by `random.Random(seed).randint(17000, 47000)`. Seeds and range are fixed before observing perturbation outcomes.

The manufacturer range spans its stated voltage and temperature conditions. We do not assert that every sampled value occurs at 25 °C or that a specific physical unit realizes every value. The CPU clock is held at its nominal modeled value; we do not vary the HSI simultaneously. Renode's RTC interrupt path and prescaler behavior still require simulator scrutiny. A frequency inside the documented bound is a necessary legality condition, not sufficient evidence that any observed failure is a brittle test.

## Measures and triage

Run the frozen selected ELF once nominally, then each of 30 seeds and both endpoints in fresh Renode processes. Record binary/test/config hashes, upstream commit, simulator version, full platform hash, seed, exact LSI frequency, virtual-time UART trace, monitor log, and case verdict. The primary unit is the selected ztest case; report flip count / evaluable seeded runs with a 95% Wilson interval, plus missing/timeouts/harness errors separately. Do not pool this selected case with the ten earlier HSI subjects as independent samples. Replay every failing seed. Apply the [four-way decision procedure](../../paper/DESIGN.md) and retain `unknown` when the RTC model or specification cannot distinguish brittleness from firmware or model error. Report the nominal full-suite pilot separately.
