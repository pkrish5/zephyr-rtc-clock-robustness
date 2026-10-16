# Phase 3 registered 100-MIPS HSI result — 2026-10-03 UTC

The [frozen plan](../subjects/phase3_hsi_100mips/plan.json) covers ten upstream selected cases and 34 source-eligible Luna suites on the pinned STM32F407/Renode setup. Each version received five fresh nominal launches; only 5/5 passes entered the same 100 seeded HSI inputs and two exact endpoints. All surviving ELF and source hashes, simulator settings, platforms, UART/monitor logs, and sampled traces passed the [raw audit](../analysis/phase3_hsi_summary.py). The one earlier sandboxed Renode launch failed before virtual time advanced and remains a separate infrastructure record outside the fresh qualification screen. The serial dispatcher later stopped at an overwrite guard when it reached an active tail-shard run; the tail worker completed that run and the audit found no duplicate record or orphan artifact. The [incident record](../results/phase3_hsi_100mips/execution_incident.json), [execution partition metadata](../results/phase3_hsi_100mips/orchestration.json), and dated amendments preserve the host-concurrency changes.

The seeded frequency-to-CPU mapping produced 99 MIPS: 27 seeds, 100 MIPS: 46 seeds, 101 MIPS: 27 seeds. Maximum absolute rounding error relative to the ideal `100 × f / 16 MHz` is 0.497 MIPS. The [STM32F407 datasheet](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) supplies the HSI ±1% bound at 25 °C; the [direct Renode probe](../results/phase3_hsi_probe/fractional_mips_probe.json) and [time-model documentation](https://renode.readthedocs.io/en/latest/advanced/time_framework.html) motivate the integer-MIPS approximation. This is a documented oscillator-input range and an approximate CPU-throughput model, not a proved silicon execution schedule.

**Evaluable seeded verdicts:** upstream selected cases 0/943 fails across 10 nominally eligible cases; Luna 0/3270 across 33 nominally eligible suites. These pooled counts are descriptive only: suites share ten tasks and every suite shares the same 100 inputs. The per-version and task tables below are the comparison units. Non-evaluable outcomes remain listed separately.

## Task-stratified overview

| Task | Upstream selected case, failures/evaluable | Luna nominally eligible / candidates | Luna failures/evaluable (descriptive) |
| --- | ---: | ---: | ---: |
| context | 0/96 | — | — |
| fifo_api | 0/83 | 5/5 | 0/500 |
| lifo_api | 0/81 | 4/5 | 0/392 |
| msgq_api | 0/83 | 5/5 | 0/479 |
| pending | 0/100 | — | — |
| queue | 0/100 | 5/5 | 0/499 |
| semaphore | 0/100 | 5/5 | 0/500 |
| sleep | 0/100 | 3/3 | 0/300 |
| timer_api | 0/100 | 4/4 | 0/400 |
| workq | 0/100 | 2/2 | 0/200 |

## Same-seed paired comparison by task

Each eligible Luna suite is paired with its task's upstream selected case on the same saved seeds. Cells below sum version-level pairs within a task for readability; repeated upstream verdicts and shared seeds mean these are correlated counts, not independent trials. The version-specific cells are in the summary JSON.

| Task | Evaluable pairs | Both pass | Both fail | Upstream only fails | Luna only fails |
| --- | ---: | ---: | ---: | ---: | ---: |
| context | — | — | — | — | — |
| fifo_api | 415 | 415 | 0 | 0 | 0 |
| lifo_api | 316 | 316 | 0 | 0 | 0 |
| msgq_api | 397 | 397 | 0 | 0 | 0 |
| pending | — | — | — | — | — |
| queue | 499 | 499 | 0 | 0 | 0 |
| semaphore | 500 | 500 | 0 | 0 | 0 |
| sleep | 300 | 300 | 0 | 0 | 0 |
| timer_api | 400 | 400 | 0 | 0 | 0 |
| workq | 200 | 200 | 0 | 0 | 0 |

## Per-version registered outcomes

A flip rate is failures divided by evaluable seeded pass/fail verdicts, with a 95% Wilson interval. Endpoint challenges are outside that denominator. `—` means a version failed the fresh nominal screen and was not varied.

| Task | Version | Nominal pass | Seeded pass | Seeded fail | Other/missing | Flip rate (95% Wilson) | Low endpoint | High endpoint |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| fifo_api | luna/fifo_api-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| fifo_api | luna/fifo_api-r02 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| fifo_api | luna/fifo_api-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| fifo_api | luna/fifo_api-r04 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| fifo_api | luna/fifo_api-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| lifo_api | luna/lifo_api-r01 | 5/5 | 92 | 0 | 8 / 0 | 0.0% (0.0–4.0%) | pass | pass |
| lifo_api | luna/lifo_api-r02 | 4/5 | 0 | 0 | 0 / 100 | — | missing | missing |
| lifo_api | luna/lifo_api-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| lifo_api | luna/lifo_api-r04 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| lifo_api | luna/lifo_api-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| msgq_api | luna/msgq_api-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| msgq_api | luna/msgq_api-r02 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| msgq_api | luna/msgq_api-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| msgq_api | luna/msgq_api-r04 | 5/5 | 89 | 0 | 11 / 0 | 0.0% (0.0–4.1%) | pass | pass |
| msgq_api | luna/msgq_api-r05 | 5/5 | 90 | 0 | 10 / 0 | 0.0% (0.0–4.1%) | pass | pass |
| queue | luna/queue-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| queue | luna/queue-r02 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| queue | luna/queue-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| queue | luna/queue-r04 | 5/5 | 99 | 0 | 1 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| queue | luna/queue-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | luna/semaphore-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | luna/semaphore-r02 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | luna/semaphore-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | luna/semaphore-r04 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | luna/semaphore-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| sleep | luna/sleep-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| sleep | luna/sleep-r02 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| sleep | luna/sleep-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| timer_api | luna/timer_api-r01 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| timer_api | luna/timer_api-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| timer_api | luna/timer_api-r04 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| timer_api | luna/timer_api-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| workq | luna/workq-r03 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| workq | luna/workq-r05 | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| context | upstream/context | 5/5 | 96 | 0 | 4 / 0 | 0.0% (0.0–3.8%) | pass | pass |
| fifo_api | upstream/fifo_api | 5/5 | 83 | 0 | 17 / 0 | 0.0% (0.0–4.4%) | pass | pass |
| lifo_api | upstream/lifo_api | 5/5 | 81 | 0 | 19 / 0 | 0.0% (0.0–4.5%) | pass | pass |
| msgq_api | upstream/msgq_api | 5/5 | 83 | 0 | 17 / 0 | 0.0% (0.0–4.4%) | pass | pass |
| pending | upstream/pending | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| queue | upstream/queue | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| semaphore | upstream/semaphore | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| sleep | upstream/sleep | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| timer_api | upstream/timer_api | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |
| workq | upstream/workq | 5/5 | 100 | 0 | 0 / 0 | 0.0% (0.0–3.7%) | pass | pass |

The [100-row paired schedule table](../results/phase3_hsi_100mips/qualified/paired_schedules.csv) keeps all registered inputs, including missing or non-evaluable outcomes. The [summary JSON](../results/phase3_hsi_100mips/qualified/summary.json) contains each task-matched upstream/Luna pass/fail cell. The original strict source gate and amended functional gate select the same 34 HSI Luna candidates before fresh screening; their difference is material in the separate RTC callback arm, not in this HSI inventory. Upstream full-application logs also contain 0 failing unrelated case verdicts across seeded runs; these are reported separately from selected-case outcomes.

## Replay and classification

0 seeded or endpoint test failures were captured. The [four-way decision ledger](../analysis/phase3_hsi_classification_decisions.json) is empty because no assertion flip required replay or classification. Counts: brittle_test_assumption=0, firmware_race_or_bug=0, simulator_or_peripheral_artifact=0, unknown=0.

Non-evaluable qualified records: 88. Fresh-process harness-error diagnostics: pass=88. Original outcomes remain unchanged. The [diagnostic index](../results/phase3_hsi_100mips/diagnostic_summary.json) preserves every run ID and diagnostic artifact.

| Version | Condition | Non-evaluable outcome | Count |
| --- | --- | --- | ---: |
| luna/lifo_api-r01 | seeded | harness_error | 8 |
| luna/lifo_api-r02 | nominal | harness_error | 1 |
| luna/msgq_api-r04 | seeded | harness_error | 11 |
| luna/msgq_api-r05 | seeded | harness_error | 10 |
| luna/queue-r04 | seeded | harness_error | 1 |
| upstream/context | seeded | harness_error | 4 |
| upstream/fifo_api | seeded | harness_error | 17 |
| upstream/lifo_api | seeded | harness_error | 19 |
| upstream/msgq_api | seeded | harness_error | 17 |

Seeded non-evaluable counts by model CPU setting: agent: 99 MIPS=8, 100 MIPS=11, 101 MIPS=11; upstream: 99 MIPS=20, 100 MIPS=19, 101 MIPS=18. Their spread across settings does not establish that missing verdicts are random; rates remain conditional on evaluable runs.

The HSI arm changes oscillator/SysTick rate with an integer CPU-throughput approximation. It does not independently vary ISR delivery delay, scheduling latency, peripheral response, or RTC LSI rate. The zero flip count is a negative result only for this frozen model and schedule set, conditional on the evaluable runs. Physical-board confirmation and independent source labels remain open. No Sol/Astra generation or repair is included.

Reproduce the derived audit and report:

```sh
python3 analysis/phase3_hsi_plan.py
python3 analysis/phase3_hsi_summary.py
python3 analysis/phase3_hsi_final_report.py
```
