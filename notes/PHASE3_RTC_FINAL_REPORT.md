# Phase 3 selected RTC paired result — 2026-10-03 UTC

All three registered 100-seed batches, five nominal repeats per version, and both endpoint challenges are complete. The raw audit checks the frozen source and ELF hashes, Renode version, CPU/SysTick/quantum, saved platform differences, seeds, and trace hashes. The same 100 distinct LSI input frequencies were used for each version. [STM32F407 DS8626 Rev. 12 Table 35](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) specifies 17–47 kHz at 3 V over −40 to 105 °C; board-level confirmation remains open.

| Test version | Nominal | Seeded pass | Seeded fail | Non-evaluable | Flip rate, evaluable seeds (95% Wilson) | 17 kHz | 47 kHz | Original strict gate | Amended functional gate |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| Repository-maintained selected case | 5/5 | 72 | 26 | harness_error 2 | 26/98 = 26.5% (18.8–36.0%) | fail | pass | n/a | n/a |
| Luna primary r04 | 5/5 | 86 | 13 | harness_error 1 | 13/99 = 13.1% (7.8–21.2%) | fail | pass | no | yes |
| Luna bound-context supplement r05 | 5/5 | 100 | 0 | 0 | 0/100 = 0.0% (0.0–3.7%) | pass | pass | no | yes |

The three original harness-error inputs (primary Luna seed 13, upstream seeds 56 and 62) each passed a separately saved fresh-process diagnostic. Their registered outcomes remain harness errors and do not enter evaluable flip denominators or paired pass/fail cells.

The original strict source gate excludes both agent versions, so it yields **no eligible agent RTC comparison**. The dated split gate admits the primary Luna r04 as functionally adequate despite its 15-second timing bound. The bound-context r05 remains a separate prompt condition and its immediate second-callback `K_NO_WAIT` check remains timing-bound inadequate, despite 0/100 observed flips. The split was retrospective and unblinded to early RTC outcomes. No row shows a model-wide improvement estimate.

## Prespecified clock-threshold check

The programmed alarm is ten RTC calendar seconds after the starting time. With the selected STM32 prescalers (128 × 250 = 32,000 LSI ticks per calendar second), calendar arrival takes approximately `320,000 / f_LSI` real seconds. Equating that duration to each source deadline gives the boundary `f_LSI = 320,000 / deadline`. A lower input frequency predicts a deadline failure. This arithmetic predicts calendar/deadline failures only; setup, polling, and delivery can shift an exact boundary, so the saved run verdict is authoritative.

| Test version | Source wait(s) | Calendar comparison window | Calendar failure boundary | Failing portion of legal 17–47 kHz range | Predicted failures among 100 seeds | Observed failures / evaluable seeds | Evaluable prediction disagreements |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Repository-maintained selected case | 3 s + 10 s | 13 s | 24,615.4 Hz | 17,000 ≤ f < 24,615.4 Hz | 26/100 | 26/98 | 0 |
| Luna primary r04 | 15 s | 15 s | 21,333.3 Hz | 17,000 ≤ f < 21,333.3 Hz | 13/100 | 13/99 | 0 |
| Luna bound-context supplement r05 | 2 s + 24 s | 26 s | 12,307.7 Hz | none (boundary below 17,000 Hz) | 0/100 | 0/100 | 0 |

The upstream 3 s plus 10 s fixed sleeps yield a 13 s arrival check and a 24,615.4 Hz boundary. Luna r04 asserts arrival within 15 s, yielding 21,333.3 Hz. The supplement first sleeps 2 s to check for a premature alarm, then waits up to 24 s for the first callback: its 26 s total calendar window yields a 12,307.7 Hz boundary, below the legal input range. These windows ignore setup time, which adds margin. Predictions match every evaluable saved seed: 26 upstream failures, 13 primary Luna failures, and zero supplement failures. The three harness-error seeds are retained as non-evaluable, so predicted counts use all 100 registered inputs while observed rates use 98, 99, and 100 evaluable runs. Endpoint behavior also agrees with the calendar calculation.

LSI-frequency variation does not independently control interrupt delivery latency or the separation between the two callback deliveries. The supplement's immediate second `k_sem_take(..., K_NO_WAIT)` can therefore hide a delivery-latency assumption even when its main 24 s deadline covers the legal clock range. Its 0/100 calendar-clock flips do **not** establish full timing-bound adequacy.

## Same-seed paired outcomes

The complete [100-row paired table](../results/phase3_rtc/paired_schedules.csv) retains every registered seed and any harness error. Pairwise counts below use only seeds with pass/fail verdicts in both versions.

| Pair (left / right) | Evaluable pairs | Both pass | Both fail | Left only fails | Right only fails |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna primary r04 / Luna bound-context supplement r05 | 99 | 86 | 0 | 13 | 0 |
| Repository-maintained selected case / Luna primary r04 | 97 | 71 | 13 | 13 | 0 |
| Repository-maintained selected case / Luna bound-context supplement r05 | 98 | 72 | 0 | 26 | 0 |

## Replay and four-way classification

Every observed seeded or endpoint failure has an individual [classification record](../analysis/phase3_rtc_classification_decisions.json), frozen raw trace, and fresh-process replay. Endpoint failures are classified but are outside seeded-rate denominators. Counts by version and category:

| Test version | Condition | Brittle test assumption | Firmware race/bug | Simulator/peripheral artifact | Unknown |
| --- | --- | ---: | ---: | ---: | ---: |
| Repository-maintained selected case | seeded | 26 | 0 | 0 | 0 |
| Repository-maintained selected case | min | 1 | 0 | 0 | 0 |
| Repository-maintained selected case | max | 0 | 0 | 0 | 0 |
| Luna primary r04 | seeded | 13 | 0 | 0 | 0 |
| Luna primary r04 | min | 1 | 0 | 0 | 0 |
| Luna primary r04 | max | 0 | 0 | 0 | 0 |
| Luna bound-context supplement r05 | seeded | 0 | 0 | 0 | 0 |
| Luna bound-context supplement r05 | min | 0 | 0 | 0 | 0 |
| Luna bound-context supplement r05 | max | 0 | 0 | 0 | 0 |

The decision procedure distinguishes a deadline assertion on otherwise allowed slow-clock behavior from firmware defects and Renode artifacts; divergent replay or insufficient evidence is retained as unknown. The STM32 peripheral model and the broad datasheet environmental range limit any physical-hardware claim. The two RTC state-observation additions are not part of this already locked three-version callback table.

Reproduce the derived audit and report from the preserved raw records:

```sh
python3 analysis/phase3_rtc_summary.py
python3 analysis/phase3_rtc_classify.py
python3 analysis/phase3_rtc_final_report.py
```
