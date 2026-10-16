# Phase 1: upstream test baseline — 2026-09-28

## Scope and status

The primary contribution chosen after Phase 0 is an empirical comparison of existing upstream tests and independently generated agent tests. Phase 1 builds the upstream side only. The ten eligible subjects here are **ten separately built ztest firmware applications from one Zephyr repository**, not ten independent upstream codebases. Each exercises SysTick, software-offloaded IRQs, or timed work on an STM32F407VG. This is an upstream-maintained proxy for human tests; individual human authorship has not been verified. It is a controlled baseline for the later same-task agent comparison, with limited external validity.

The detailed inclusion rule and schedule were [registered before perturbed runs](../subjects/phase1_zephyr/PROTOCOL.md). The machine-readable [candidate manifest](../subjects/phase1_zephyr/candidates.json), [builds](../results/phase1/builds.jsonl), [runs](../results/phase1/runs.jsonl), [summary](../results/phase1/summary.json), and [environment](../results/phase1/environment.json) are preserved.

## Candidate corpus and nominal gate

| Firmware test application | Interrupt or timer path | Nominal ztest cases |
| --- | --- | ---: |
| `timer_api` | SysTick timer callback | 15 pass |
| `semaphore` | IRQ-offloaded semaphore operations | 29 pass |
| `fifo_api` | IRQ-offloaded FIFO operations | 8 pass |
| `lifo_api` | IRQ-offloaded LIFO operations | 5 pass |
| `msgq_api` | IRQ-offloaded message queue operations | 18 pass |
| `workq` | Scheduled work and timer interrupts | 27 pass, 3 skip |
| `queue` | IRQ-offloaded queue operations | 26 pass |
| `sleep` | SysTick wakeups | 3 pass |
| `context` | IRQ-offloaded and timer interrupts | 6 pass, 3 skip |
| `pending` | Timer-driven pending work | 3 pass |
| `exti_stm32` | STM32 EXTI software interrupt | **3 fail; excluded** |

All 11 source applications built from unchanged Zephyr v4.3.0 test files at commit `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`; 10 passed nominally and have 140 passing test cases plus six skipped cases. The EXTI candidate failed its pending-bit assertion in all three cases before perturbation. Its [UART log](../results/phase1/uart_logs/exti_stm32-nominal-000-mips16.log) is retained. We do not count it as a flip or assume its cause without further model validation.

## Bounded clock perturbation and measurement

The study-owned [DTS overlay](../subjects/phase1_zephyr/config/stm32f4_hsi.overlay) selects the STM32F407's 16 MHz HSI clock in place of Zephyr's default external-oscillator/PLL board setting. The [ST datasheet](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf) bounds HSI accuracy at 25 °C to ±1%. The primary schedule set consists of 30 seeded integer frequencies in **15.84–16.16 MHz**, plus exact endpoint challenges reported separately. Each full ztest ELF and upstream source tree is hashed and unchanged across its nominal and perturbed runs. Renode 1.17.0's SysTick frequency is the only varied model parameter; its CPU throughput is fixed at 16 MIPS and the synchronization quantum at 1 µs. [Renode's CPU MIPS setting is integer](https://renode.readthedocs.io/en/latest/advanced/time_framework.html), so this model does not reproduce coupled ±1% CPU clock drift exactly. The oscillator values are hardware bounded, but the resulting simulator schedules are **model limited**; see [threats](../paper/THREATS.md). A positive flip needs artifact/unknown classification until the coupling is validated.

Every run records the ELF and test-source hashes, upstream commit, simulator version, seed, clock value, full platform hash, UART observation trace, and monitor output. The [analysis script](../analysis/phase1_summary.py) checks hashes and schedule mapping before computing suite- and case-level flip rates with Wilson intervals. A failing run must be replayed in a fresh Renode process with [replay.py](../harness/phase1/replay.py); unresolved causes stay **unknown** in the four-way classification table.

## Perturbed baseline

All **300 prespecified subject–seed runs** were recorded. Among nominally passing suites, **299 passed, zero failed, and one ended in a harness error** before any virtual time advanced. Thus there were **0 observed pass-to-fail flips in 299 evaluable runs**, with one unresolved run retained. This is a descriptive count, not a pooled binomial estimate: the same seed set and board are shared across subjects. Each suite also passed both exact endpoint challenges, 15.84 and 16.16 MHz (20/20 additional runs). The 30 random seeds sampled 15,862,677–16,140,846 Hz; endpoints are outside this sampled span and are reported separately.

| Upstream suite | Evaluable seeded runs | Flips | Unresolved | 95% Wilson interval for flip rate |
| --- | ---: | ---: | ---: | ---: |
| `timer_api` | 30 | 0 | 0 | 0–11.35% |
| `semaphore` | 30 | 0 | 0 | 0–11.35% |
| `fifo_api` | 30 | 0 | 0 | 0–11.35% |
| `lifo_api` | 30 | 0 | 0 | 0–11.35% |
| `msgq_api` | 30 | 0 | 0 | 0–11.35% |
| `workq` | 30 | 0 | 0 | 0–11.35% |
| `queue` | 30 | 0 | 0 | 0–11.35% |
| `sleep` | 29 | 0 | 1 | 0–11.70% |
| `context` | 30 | 0 | 0 | 0–11.35% |
| `pending` | 30 | 0 | 0 | 0–11.35% |

The `sleep` seed 19 record is a Renode startup `pexpect.TIMEOUT` with monitor output only `R`, no UART case result, and `virtual_ns = 0`. A fresh-process replay with the same ELF, seed, platform, and simulator version **passed**. The original remains an unresolved harness error in the primary data; [the replay record](../results/phase1/replays.jsonl) documents its divergence. The excluded `exti_stm32` candidate failed its pending-bit assertion at nominal and on all 30 sampled frequencies. It was inadvertently included in the batch runner's default all-subject loop; all its raw records are retained, and none enters a flip numerator or denominator. Its cause is still unknown. **All 31 EXTI failures replayed with identical sampled traces and verdicts** in fresh Renode processes. The [analysis script](../analysis/phase1_summary.py) revalidated saved platform, UART, and trace hashes and checked each run's ELF, source, and overlay hashes against the build manifest before producing the final [summary](../results/phase1/summary.json).

The [four-way flip classification table](../results/phase1/classifications.json) is empty because no eligible test flipped. The zero observed flip rate is a useful **negative result for this narrow model-limited clock setting**. It does not show that upstream tests lack timing assumptions, nor does it establish that an agent can improve them. The current corpus emphasizes Zephyr kernel API suites, includes few external interrupt stimulus tests, uses one board and one repository, and has no completed agent arm. A legal, independently timed stimulus or peripheral response dimension would likely give RQ2 more discrimination if its hardware bound and Renode model can be verified first. The available choices are recorded in [DESIGN.md](../paper/DESIGN.md).

## Reproduce

Run from a fresh copy of this workspace or an empty Phase 1 results directory; the build/run tools preserve raw outputs and refuse overwrites. The source tree in `subjects/upstream/zephyr` is pinned and clean. Follow the [host setup recipe](../harness/phase1/SETUP.md) for Zephyr SDK 0.17.4 ARM, Python 3.12 for `west`, project-local CMake 3.31.10, and Renode 1.17.0. The exact installed environment and component revisions are in `results/phase1/environment.json`. After setting up these dependencies:

```sh
python3 harness/phase1/build_subjects.py
python3 harness/phase1/run.py --condition nominal --count 1 --cpu-mips 16 --max-virtual-sec 90
python3 harness/phase1/run.py --condition perturbed --start 0 --count 30 --cpu-mips 16 --max-virtual-sec 90
python3 harness/phase1/run.py --condition min --count 1 --cpu-mips 16 --max-virtual-sec 90
python3 harness/phase1/run.py --condition max --count 1 --cpu-mips 16 --max-virtual-sec 90
python3 harness/phase1/replay.py --all-failures
python3 analysis/phase1_summary.py
```

## Interpretation and next gate

The selected subjects are mostly Zephyr kernel API test applications. They provide an upstream-maintained comparison on exactly the same firmware features and board planned for agent generation, but they do not establish population rates across vendors or codebases. The later agent arm must preserve the same specifications, board configuration, schedule set, and oracle checks. No agent suite or repair was generated in Phase 1. **Phase 1 stops here for review.** The recommended next decision is whether to validate an additional independently timed interrupt/peripheral dimension before agent generation, since the current HSI-only arm observed no flips and has a CPU-clock coupling limitation.
