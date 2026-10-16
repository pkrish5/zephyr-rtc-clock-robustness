# Phase 0 feasibility spike — 2026-09-28

## Verdict

**GO for the core simulation mechanism.** With one frozen STM32F407 ELF and frozen test files, documented ±1% HSI clock variation produced 27 fixed-sleep verdict flips in 100 seeded schedules, while an event-wait test passed all 100. Both tests passed 100/100 at nominal timing. All 27 failing seeds replayed with exactly the same sampled event trace and verdict in a fresh Renode process. This is a deliberately authored fixture, so it establishes feasibility, **not** agent prevalence, a human baseline, or silicon accuracy.

| Test | Nominal passes | Perturbed passes | Flip rate, 95% Wilson interval |
| --- | ---: | ---: | ---: |
| Fixed 10.05 ms sleep | 100/100 | 73/100 | 27/100 = 27.0% [19.3%, 36.4%] |
| Wait for GPIO event, 12 ms deadline | 100/100 | 100/100 | 0/100 = 0.0% [0%, 3.7%] |

The generated [summary](../results/phase0/summary.json) and [classification table](../results/phase0/classifications.json) assign the 27 flips to **brittle test assumption**: at the fixed check, GPIO and ISR count are both zero; under the same seed, the event-wait test sees the GPIO bit high and ISR count one by 11 ms. The highest failing frequency was 15,919,275 Hz; the lowest passing frequency was 15,926,481 Hz, bracketing the predicted boundary near 15.920 MHz. There were zero observed firmware-bug, model-artifact, or unknown classifications for this fixture. These labels do not remove the untested risk of model error on physical hardware.

## Simulator and legality

Renode was selected because its [virtual-time framework](https://renode.readthedocs.io/en/latest/advanced/time_framework.html) exposes CPU performance and synchronization quantum, its [hooks](https://renode.readthedocs.io/en/latest/basic/using-python.html) expose interrupt entry/exit and bus access, and its [peripheral scheduling mechanisms](https://renode.readthedocs.io/en/latest/networking/machine-to-machine-connections.html) support timed model events. The packaged [STM32F4 platform](https://github.com/renode/renode/blob/master/platforms/cpus/stm32f4.repl) exposes `systickFrequency`. The runner saves the exact platform text used for each frequency. Zephyr [Twister](https://docs.zephyrproject.org/latest/develop/twister/index.html) lists Renode simulation and board metadata, but no Zephyr build was attempted in this spike.

QEMU's [`-icount`](https://www.qemu.org/docs/master/system/qemu-manpage.html) provides deterministic virtual instruction time but is explicitly not cycle accurate; its [record/replay](https://www.qemu.org/docs/master/system/replay.html) logs nondeterministic inputs. We did not find a comparably direct, documented STM32F4 SysTick-frequency control in QEMU, so QEMU remains a cross-simulator candidate rather than the Phase 0 runner. The full control-by-control survey is in [`paper/DESIGN.md`](../paper/DESIGN.md).

The [STM32F407 datasheet](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf) specifies 16 MHz HSI as the reset CPU clock and an HSI accuracy of −1% to +1% at 25 °C (DS8626 Rev 12, Table 34). The [Cortex-M4 programming manual](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf) states that SysTick uses the processor/AHB clock when `CLKSOURCE=1`; the firmware selects that setting. Each seed samples an integer frequency uniformly from **15,840,000–16,160,000 Hz**. Renode's synchronization quantum stayed at 1 µs; its CPU `PerformanceInMips` was not varied and is not treated as a hardware clock bound.

## What ran

- Firmware: [`subjects/phase0_stm32f4_systick/firmware.elf`](../subjects/phase0_stm32f4_systick/firmware.elf), SHA-256 `e0d0fa9c976461defabdb53fb3112d1be883c795d5b343e1be73ef391b718cc6`. The SysTick ISR raises GPIOD pin 12 after 160,000 timer clocks.
- Tests: [`fragile.py`](../harness/phase0/fragile.py), SHA-256 `19c62af2a2bcb8fce1b8bce386bcfb6c62e83c5950a7d23f51b6d96136663d25`; [`robust.py`](../harness/phase0/robust.py), SHA-256 `53843098babe8c1108ac5d1060ec6af4934f6638ec387cde6aa899dc7325a6f3`. Both assert the same GPIO bit; only the waiting strategy differs.
- Simulator: Renode 1.17.0, build `1.17.0+20260906gitf1dd1b4af`, .NET 8.0.21, Apple Silicon portable package. Build tools: Apple Clang 21.0.0 and GNU Arm binutils 2.47.20260726. Runner: Python 3.14.6 and pexpect 4.9.0.
- Raw evidence: 400 [JSONL run records](../results/phase0/runs.jsonl), 400 per-test JSON traces in `results/phase0/traces/`, 200 Renode console logs, 27 [replay records](../results/phase0/replays.jsonl), 27 replay logs, and saved platform configurations. Every run record includes the firmware and test hashes, simulator version, seed, frequency, platform hash, quantum, trace path, and verdict.

Example: seed 1 maps to 15,910,445 Hz. Its [fragile trace](../results/phase0/traces/perturbed-001-fragile.json) samples GPIO low at 10.05 ms; its [event-wait trace](../results/phase0/traces/perturbed-001-robust.json) samples GPIO high at 11 ms. A fresh-process replay of the failing test matched the original trace and verdict.

## Reproduce

Run from a fresh copy of this workspace that does not already contain `results/phase0/` run files; the runner preserves raw results and refuses duplicate traces. On Apple Silicon macOS:

```sh
curl -L --fail -o /private/tmp/renode-1.17.0.osx-arm64-portable.dmg https://github.com/renode/renode/releases/download/v1.17.0/renode-1.17.0.osx-arm64-portable.dmg
shasum -a 256 /private/tmp/renode-1.17.0.osx-arm64-portable.dmg
# Expected: 63b1fb691207f503cea937e4ec8fad3e068a517d0abac3c24c0206c62f6c4d12
hdiutil attach -readonly -nobrowse -mountpoint /private/tmp/renode-mounted /private/tmp/renode-1.17.0.osx-arm64-portable.dmg
brew install arm-none-eabi-binutils
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r harness/phase0/requirements.txt
sh subjects/phase0_stm32f4_systick/build.sh
RENODE_BIN=/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode python3 harness/phase0/run.py batch --condition both --count 100
RENODE_BIN=/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode python3 harness/phase0/run.py replay-all
python3 analysis/phase0_summary.py
```

To inspect one existing failure: `python3 -c 'import json; print([json.loads(s) for s in open("results/phase0/runs.jsonl") if "perturbed-001-fragile" in s][0])'`. The direct replay command is `RENODE_BIN=... python3 harness/phase0/run.py replay --seed 1` in a fresh results copy (the current copy already contains that replay and deliberately rejects duplicates).

## What did not work, and limits

The workspace lacked a Zephyr checkout/toolchain, so the spike used a purpose-built bare-metal firmware instead of a Zephyr sample with ztest tests. This still proves the scheduling mechanism, but does not validate the planned human comparison. The first automated attempt also encountered Renode log text interleaving with its console prompt; its partial output is retained under `results/phase0/aborted/`, and the corrected harness reran the trial. QEMU was surveyed from official documentation but not installed or executed.

The traces sample GPIO state at test observation times and include final ISR count; they are not instruction-level or exact interrupt-entry traces. The 12 ms event-wait deadline is a test design choice, not a manufacturer end-to-end latency guarantee. Renode's CPU performance is an abstract timing model, and the simulator has not been compared with physical STM32F4 hardware. One hundred identical nominal reruns establish stability of this deterministic setup, not 100 independent schedules. The Wilson intervals describe only the specified uniform frequency sampling scheme.

**Next decision after review:** Port a Zephyr interrupt sample and ztest suite on a well-modeled board before building the Phase 1 corpus. The STM32F4 Discovery is the concrete physical-board candidate; [Zephyr documents the board](https://docs.zephyrproject.org/latest/boards/st/stm32f4_disco/doc/index.html) and Renode ships its platform model. No hardware purchase is needed for this decision. Stop here for Phase 0 review.
