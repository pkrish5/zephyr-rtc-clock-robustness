# RTC/LSI threshold-validation amendment — 2026-10-04

**Historical status:** the 66-suite forecast remains frozen, but the 12-suite sample described below was superseded before any new varied run by the [balanced 14-suite amendment](RTC_BALANCED_SPEC_CONTEXT_AMENDMENT.md). Keep this document and its v1 sample lock as an audit trail; use the v2 sample for any approved execution. No new factorial varied-timing run has started.

## Rationale and scope

The full RTC arm would require about 113 serial machine-hours before replay. In the historical selected RTC callback experiment, the clock-derived failure sets matched every evaluable seeded verdict: 26 upstream failures, 13 primary Luna failures, and zero supplement failures, with no false-positive threshold calls. This is encouraging selected-case evidence, not an estimate of predictive accuracy on the new 66 suites. The prospective sample tests that method while saving simulation time. The 100-MIPS HSI factorial arm is deferred after the prior null result of 0 assertion flips in 4,213 evaluable seeded runs; its startup errors and model limits remain recorded.

The [authoritative forecast](../analysis/rtc_threshold_sample_v1/forecast.json), [sample manifest](../analysis/rtc_threshold_sample_v1/sample.json), and [hash lock](../analysis/rtc_threshold_sample_v1/lock.json) fix source/ELF hashes, schedule hash, each source expression, per-seed predictions, sampling seed, exact selected suites, and the agreement/fallback rule. The [66-row CSV](../analysis/rtc_threshold_sample_v1/forecast_table.csv) is a readable export. `python3 analysis/freeze_rtc_threshold_sample.py` verifies the frozen files without overwriting them. No experimental result was used to choose new-suite classifications or sample members.

## Prediction rule

The registered LSI frequencies are the exact 100 integers in `subjects/phase3_rtc/plan.json`, all within 17–47 kHz. Under the fixed 128×250 RTC prescaler, ten calendar seconds take `320000/f_LSI` host seconds. For a source with a single decipherable observation budget `B`, the **clock-only hypothesis** predicts failure for a seed when `320000/f_LSI > B`. Equality is treated as predicted pass; none of the selected short-deadline seeds lands exactly on a boundary. Source-level calendar conversion, peripheral readback, and other assertions are assumed to behave as at nominal timing. Zephyr thread service, polling overhead, and Renode peripheral behavior are not bounded by the oscillator specification; the sampled runs challenge these assumptions. A prediction is never described as a measured verdict or a hardware guarantee.

All 27 eligible RTC counting suites poll calendar progress with a 20–60 s observation budget. The slowest legal ten-second calendar advance is about 18.824 host seconds, so each has a frozen **0/100** clock-only failure prediction. Three simple alarm-pending suites have short first/overall deadlines:

| Suite | Source budget | Failure boundary | Predicted failures / 100 |
|---|---:|---:|---:|
| `sol-range_absent-rtc_alarm_pending-r01` | 16 s | `f_LSI < 20,000 Hz` | 11 |
| `sol-range_absent-rtc_alarm_pending-r03` | 15 s first calendar window | `f_LSI < 21,333.3 Hz` | 13 |
| `astra-range_absent-rtc_alarm_pending-r05` | 15 s overall window | `f_LSI < 21,333.3 Hz` | 13 |

These three pending forecasts assume the Renode peripheral's alarm-pending flag becomes observable promptly after the calendar compare. That is a **falsifiable model assumption**. The 19 callback suites are `not_predictable` because callback IRQ delivery and callback-to-thread ordering lack a clock-only bound. The other 17 pending suites are `not_predictable` because pending-bit service, setup, polling phase, or multiple deadlines can decide their verdict without a unique LSI-rate boundary. All 36 such suites receive the complete schedule; no predicted count is imputed for them. The [CSV](../analysis/rtc_threshold_sample_v1/forecast_table.csv) gives every individual status and reason.

## Frozen selection and validation

Use `random.Random(20261004)` on sorted suite IDs. Include all three nonzero-prediction suites with certainty. In each remaining model × range-condition × task-family stratum that has predictable suites, randomly choose one. Fill to **12 predictable suites** by a seeded uniform draw without replacement from the remaining predictable suites. The sample covers all eight predictable strata. The 36 not-predictable suites run in full, covering every other eligible stratum as well. The certainty additions intentionally enrich boundary tests; unweighted sample rates are not representative of all 30 predictable suites.

| Model | Range | RTC family | Eligible | Predicted | Not predictable, full | Predicted sampled |
|---|---|---|---:|---:|---:|---:|
| Luna | Absent | Counting | 4 | 4 | 0 | 1 |
| Luna | Present | Counting | 3 | 3 | 0 | 1 |
| Sol | Absent | Callback | 5 | 0 | 5 | 0 |
| Sol | Absent | Counting | 5 | 5 | 0 | 2 |
| Sol | Absent | Pending | 5 | 2 | 3 | 2 |
| Sol | Present | Callback | 5 | 0 | 5 | 0 |
| Sol | Present | Counting | 5 | 5 | 0 | 1 |
| Sol | Present | Pending | 5 | 0 | 5 | 0 |
| Astra | Absent | Callback | 5 | 0 | 5 | 0 |
| Astra | Absent | Counting | 5 | 5 | 0 | 1 |
| Astra | Absent | Pending | 5 | 1 | 4 | 1 |
| Astra | Present | Callback | 4 | 0 | 4 | 0 |
| Astra | Present | Counting | 5 | 5 | 0 | 3 |
| Astra | Present | Pending | 5 | 0 | 5 | 0 |
| **Total** | | | **66** | **30** | **36** | **12** |

For every sampled predictable suite, **all 100 original seeded verdicts must be evaluable and match the entire frozen pass/fail vector exactly**. A matching failure count on different seeds fails the criterion. A harness error is non-evaluable and leaves validation inconclusive; keep the original record and diagnose separately. If any evaluable seed disagrees, report that suite's observed results, replay the exact failing input, classify the discrepancy (brittle assumption, firmware bug, simulator artifact, or unknown), and present an expansion proposal for user review. Do not expand the sample or rewrite predictions autonomously. Endpoint challenges are reported separately and do not enter this criterion.

Even perfect sample agreement does not prove the 18 unsampled suites. All 18 have a **predicted 0/100** count; they will be reported in a dedicated *prediction-only* table, without measured flip rates or Wilson intervals. The sampled and not-predictable suites have measured outcomes in a separate table. Cross-model or upstream empirical comparisons may use measured suites only, with task clustering and unequal sample inclusion acknowledged; prediction-only rows cannot be pooled as observations.

## Runtime estimate and review stop

The proposed primary scan runs `(36 not predictable + 12 sampled predictable) × (100 seeds + 2 endpoints) = 4,896` fresh Renode processes. At the historical RTC seeded mean of 60.4 wall seconds, this is about **82 serial machine-hours**, or **27 hours with ideal three-worker scaling**. The full 66-suite scan was about 113 serial hours, so the base saving is roughly 31 serial hours. Runtime remains uncertain because these new suites differ from the historical callback trio. Every observed assertion failure requires exact replay; harness diagnostics and the two RTC state upstream baselines add time. We do not infer a replay count in advance.

**Proposed sample size: 12 predictable suites, plus all 36 not-predictable suites. Stop here for user approval before running either RTC/LSI or deferred HSI schedules.**
