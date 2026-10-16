# Phase 1 human baseline protocol (registered before perturbed runs)

Date: 2026-09-28. This is a **pilot baseline** for independent upstream Zephyr ztest applications, not a claim about all embedded tests or other open-source projects.

## Eligibility and denominator

The [candidate manifest](candidates.json) lists 11 interrupt-involving ztest applications from Zephyr v4.3.0, commit `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`. All use STM32F4 Discovery / STM32F407VG. Ten passed nominally. `exti_stm32` built but all three cases failed nominally in Renode; it remains in the build and run logs and is excluded from flip rates. Its reason is under investigation and it is not counted as a timing flip. The corpus is ten separate full firmware test ELFs from one upstream repository, so project and board diversity are limited.

The primary unit is a ztest application (subject). For each eligible subject, the primary timing sample is **30 distinct prespecified seeds, 0–29**, mapped to integer frequencies uniformly over 15,840,000–16,160,000 Hz using Python's `random.Random(seed).randint`. The nominal condition is 16,000,000 Hz. Two exact endpoints are additional challenge schedules, reported separately from the random-sample flip rate. The same schedule set is applied to every subject. Report pass/fail/timeout/harness-error and skip counts; nominally failing subjects are retained in an exclusion table. The full 100-seed experiment belongs in Phase 3, after agent tests are frozen.

Compute per-subject flip rate as the number of random schedules that change a nominal pass to fail divided by 30, with a 95% Wilson interval. Do not count timeout or harness errors as passing or silently remove them; report them separately and classify unresolved outcomes unknown. Do not pool per-test cases as if independent subjects. Report aggregate descriptive counts with a subject-level interval or explicitly mark them descriptive.

## Legal timing input

The [STM32F407 datasheet](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf) gives the 16 MHz HSI oscillator a ±1% accuracy at 25 °C. The [clock overlay](config/stm32f4_hsi.overlay) selects HSI as the Zephyr board's system clock. This matters because upstream `stm32f4_disco.dts` otherwise uses an 8 MHz HSE and 168 MHz PLL. The runner changes only Renode's `systickFrequency` within the stated HSI bound, preserves each ELF and test source across schedules, and records the full platform text hash, test-source tree hash, ELF hash, seed, UART observation trace, monitor log, and simulator version. Renode's 1 µs synchronization quantum remains fixed. Its CPU throughput is set to 16 MIPS for all primary runs; [Renode documents](https://renode.readthedocs.io/en/latest/advanced/time_framework.html) this parameter as an integer, so a ±1% proportional change cannot be represented at 16 MIPS. The oscillator input is inside a documented hardware range, but the simulated CPU-to-SysTick relationship is only an approximation of coupled clock drift. We therefore treat this as a **model-limited baseline**, not a conclusive hardware-legal schedule set. Any flip plausibly caused by this approximation must be classified artifact or unknown until validated; no unsupported latency bounds are introduced.

## Baselines and exclusions

The nominal 100 MIPS `timer_api` run is retained as a setup pilot and excluded from primary rates. The primary simulator configuration is 16 MIPS. Static sleep/timeout tagging, agent generation, repair, and hardware validation are later phases. Upstream test source stays unchanged; the study's board overlay is tracked separately. The known Renode EXTI failure illustrates why nominal compatibility is an explicit gate.
