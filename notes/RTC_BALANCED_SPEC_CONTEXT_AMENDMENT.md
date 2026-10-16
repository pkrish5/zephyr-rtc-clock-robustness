# Balanced RTC sample and primary spec-context comparison — 2026-10-04

**Status:** frozen before new factorial varied runs; awaits user approval. This amendment changes the validation sample, not the 66-suite source forecast, registered 100 LSI frequencies, frozen sources/ELFs, or the requirement to run every `not_predictable` suite. The [original 12-suite sample](../analysis/rtc_threshold_sample_v1/sample.json) is superseded and preserved. The [v2 hash lock](../analysis/rtc_threshold_sample_v2/lock.json) and [v2 sample](../analysis/rtc_threshold_sample_v2/sample.json) are authoritative; the [66-row v2 table](../analysis/rtc_threshold_sample_v2/forecast_table.csv) shows which suites would be measured.

## Balanced, seeded selection

The user asked for prompt balance within each model. Of 30 suites with frozen clock-only forecasts, sample **14**: Luna 2 range-absent and 2 range-present, Sol 3 and 3, Astra 2 and 2. Certainty-include the three nonzero forecast cases (11, 13, 13 failures), draw one suite using `random.Random(20261004)` from every remaining uncovered model × prompt × RTC-family stratum, then fill the fixed quotas without replacement from sorted IDs. All eight strata that contain predictable suites are represented. The certainty cases and quotas are disclosed; this is a seeded stratified validation sample, not a simple random sample for prevalence estimation.

| Model | Predictable sampled, absent | Predictable sampled, present | Other suites run in full, absent/present | All eligible, absent/present |
|---|---:|---:|---:|---:|
| Luna | 2 | 2 | 0 / 0 | 4 / 3 |
| Sol | 3 | 3 | 8 / 10 | 15 / 15 |
| Astra | 2 | 2 | 9 / 9 | 15 / 14 |
| **Total** | **7** | **7** | **17 / 19** | **34 / 32** |

The exact sampled predictable IDs are:

| Model | Range absent | Range present |
|---|---|---|
| Luna | `rtc_time_counting-r01`, `rtc_time_counting-r03` | `rtc_time_counting-r01`, `rtc_time_counting-r02` |
| Sol | `rtc_alarm_pending-r01`, `rtc_alarm_pending-r03`, `rtc_time_counting-r03` | `rtc_time_counting-r01`, `rtc_time_counting-r04`, `rtc_time_counting-r05` |
| Astra | `rtc_alarm_pending-r05`, `rtc_time_counting-r02` | `rtc_time_counting-r01`, `rtc_time_counting-r05` |

All 36 `not_predictable` suites run the full registered 100-seed list and two endpoints. The 14 sampled predictable suites do likewise. This is **50 × 102 = 5,100** fresh Renode processes: 5,000 primary seeded verdicts and 100 endpoint challenges. Sixteen predictable suites are not run; all have frozen **0/100** clock-only forecasts and must be labeled prediction-only. At the earlier RTC seeded mean of 60.4 wall seconds, the base scan is about **86 serial machine-hours** or **29 hours under ideal three-worker scaling**, before replays, contention, and two RTC state upstream baselines. This adds about 3.4 serial hours to the superseded 12-suite sample and remains below the estimated 113-hour full arm.

## Preregistered primary comparison

The user selected a **hybrid all-eligible rate** because 36 suites cannot be predicted from LSI frequency alone. For each of the 66 eligible suites and each of the 100 fixed seed IDs, use the original measured verdict if that suite runs; use the frozen forecast only for one of the 16 unsampled suites. The latter are imputed predictions, not observed passes. For each model × prompt condition × RTC task family, calculate `failures / (100 × eligible suites in that cell)`, showing measured and prediction-only contributions separately. Endpoint results do not enter the rate.

The primary contrast is range-present minus range-absent. Calculate it first within each model × family. Average family contrasts equally within each model: Luna has counting only; Sol and Astra each have callback, counting, and pending. Average the three model contrasts equally for the pooled result. Negative means fewer failures with range information. This uses all 66 suites and prevents large cells from silently dominating. Report each family contrast, raw cell rates, a suite-weighted pooled sensitivity estimate, and measured-only contrasts. Do not treat the pooled difference as an independently sampled firmware-project effect; the task families and generated suites are clustered and Luna lacks eligible callback/pending suites.

The hybrid point comparison is **conditional on exact per-seed agreement for all 14 sampled predictable suites**: each must have 100 evaluable original verdicts and an exact 100-bit pass/fail match to the frozen forecast. Equal counts on different seeds do not pass. Any evaluable mismatch triggers exact replay, four-way classification, and a user-reviewed proposal on whether to expand sampling. Harness errors remain non-evaluable; diagnose separately without changing original records. If validation is incomplete or fails, report measured outcomes and prediction discrepancies, but do not call the all-eligible hybrid estimate validated. If an original seeded outcome is missing, show lower/upper rate bounds by assigning missing outcomes pass/fail; no diagnostic verdict is silently imputed.

Measured suites retain per-suite Wilson intervals and replay/classification records. The 16 prediction-only suites receive **no measured flip rate or Wilson interval**. Even 14/14 exact validation does not prove their outcomes; display their forecast table separately from measured data. The original strict-gate view remains secondary, with the same observed/predicted distinction. The HSI factorial arm remains deferred after the prior 0/4,213 evaluable null. **No varied run starts before user approval.**
