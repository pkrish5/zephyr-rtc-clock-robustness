# RTC v2 clock variation arm — final audited report (2026-10-06 UTC)

**Status, updated 2026-10-07 UTC:** the approved RTC/LSI arm, reduced reference-oracle triage, and three validated timing-mutant quality challenges are complete. This report keeps their results separate. The separately approved delivery-delay pilot stopped at a failed one-tick reference smoke before any suite verdict run and is deferred to future work. The HSI factorial arm remains deferred.

## Execution and integrity

The [frozen manifest](../results/rtc_factorial_v2/manifest.json) registered 53 measured suites: 14 sampled clock-predictable AI suites, all 36 not-predictable AI suites, and three matched upstream human selected cases. Three suite-disjoint workers each completed. All **5,406/5,406** original records exist: 5,300 seeded runs and 106 endpoint challenges. The seeded outcomes are **5,182 pass, 106 assertion fail, 12 harness error**; the endpoints are **100 pass, six assertion fail** (all at 17 kHz). The 12 original Renode monitor timeouts remain missing verdicts, with no diagnostic substitution. Seven occurred before virtual time advanced and five after 3.5–14.5 virtual seconds; all 12 were in Sol not-predictable suites. Their suite IDs and seed frequencies are in the [machine-readable audit](../analysis/rtc_factorial_v2_final_summary.json).

The [final audit script](../analysis/rtc_factorial_v2_final_audit.py) checks unique 100-seed/two-endpoint coverage, registered LSI frequencies and simulator settings, frozen source/ELF hashes in each record, saved trace hashes, all 14 sampled exact pass/fail vectors, replay coverage, persisted trace fields, and the separate classification ledger. It passed. **All 14/14 sampled predictable suites have 100/100 evaluable seeds and exact per-seed agreement** with their prospectively frozen forecasts. No prediction-mismatch stop marker appeared. The other 16 predictable suites were not run; all have frozen 0/100 predictions. This is validation of the specified sample criterion, not measurement of those 16 outcomes.

Every one of the **112 original assertion failures** (106 seeded, six endpoints) has one fresh-process replay with the same verdict and identical saved LSI frequency, observations, cases, outcome, and error fields. The active runner's raw `identical_trace_and_verdict=false` flag is known to be false because it compared an in-memory tuple with a JSON list; the [persisted-trace audit](../analysis/rtc_factorial_v2_replay_audit.py) supplies the reported equality and does not change raw files. The [classification ledger](../analysis/rtc_factorial_v2_classification.json) assigns all 112 to **brittle test assumption**, using the frozen assertion, legal LSI value, calculated clock boundary, and matching replay. There are zero observed firmware-bug, simulator-artifact, or unknown *assertion failures* under this source-backed rule. Harness errors remain 12 missing verdicts, and the proposed reference-oracle triage may change these provisional failure attributions after separate approval.

## Same-schedule human comparison and AI cells

Each cell below contains the complete 100-seed schedule for every listed suite. `Measured fail` counts assertion failures in original runs. `Predicted fail` counts frozen forecasts in unrun suites. `Missing` counts original harness errors. A bracket is the possible all-eligible failure-rate range if every missing verdict were respectively pass or fail; it is **not** a confidence interval. A singleton is still partly prediction-based when `Pred` is nonzero. The human rates are measured only: callback **26/100** (95% Wilson 18.4–35.4%), counting **17/100** (10.9–25.6%), pending **26/100** (18.4–35.4%). Wilson intervals for each measured AI suite and measured cell are in the [read-only summary](../analysis/rtc_factorial_v2_summary.py).

| Task | Model | Prompt | Eligible suites | Measured / predicted suites | Measured fail | Predicted fail | Missing | Hybrid rate bound |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Callback | Human | — | 1 | 1 / 0 | 26 | 0 | 0 | 26.0% |
| Callback | Sol | Absent | 5 | 5 / 0 | 0 | 0 | 1 | 0–0.2% |
| Callback | Sol | Present | 5 | 5 / 0 | 0 | 0 | 6 | 0–1.2% |
| Callback | Astra | Absent | 5 | 5 / 0 | 0 | 0 | 0 | 0% |
| Callback | Astra | Present | 4 | 4 / 0 | 0 | 0 | 0 | 0% |
| Counting | Human | — | 1 | 1 / 0 | 17 | 0 | 0 | 17.0% |
| Counting | Luna | Absent | 4 | 2 / 2 | 0 | 0 | 0 | 0% |
| Counting | Luna | Present | 3 | 2 / 1 | 0 | 0 | 0 | 0% |
| Counting | Sol | Absent | 5 | 1 / 4 | 0 | 0 | 0 | 0% |
| Counting | Sol | Present | 5 | 3 / 2 | 0 | 0 | 0 | 0% |
| Counting | Astra | Absent | 5 | 1 / 4 | 0 | 0 | 0 | 0% |
| Counting | Astra | Present | 5 | 2 / 3 | 0 | 0 | 0 | 0% |
| Pending | Human | — | 1 | 1 / 0 | 26 | 0 | 0 | 26.0% |
| Pending | Sol | Absent | 5 | 5 / 0 | 24 | 0 | 3 | 4.8–5.4% |
| Pending | Sol | Present | 5 | 5 / 0 | 0 | 0 | 2 | 0–0.4% |
| Pending | Astra | Absent | 5 | 5 / 0 | 13 | 0 | 0 | 2.6% |
| Pending | Astra | Present | 5 | 5 / 0 | 0 | 0 | 0 | 0% |

The **measured AI seeded count is 37 failures in 5,000 original runs**, with 12 missing verdicts; all 37 failures occur in three range-absent pending suites: Sol r01 (11), Sol r03 (13), and Astra r05 (13). Their 11/13/13 observed vectors exactly match the frozen clock predictions. A zero in the table means only that no clock-induced failure was observed or predicted under this schedule. It does not establish full timing-bound adequacy, especially for asynchronous delivery assumptions.

Put plainly, **all 37 AI clock failures came from three range-absent suites**: 37/2,400 measured range-absent suite–seed opportunities, versus **zero failures among 2,600 measured range-present opportunities**. The absent and present cells had four and eight original harness errors, respectively, which remain missing verdicts. Including the 16 unrun, prediction-only eligible suites gives hybrid denominators of 37/3,400 absent and 0/3,200 present; those larger denominators combine measured outcomes with frozen forecasts and must not be presented as fully measured rates.

### Model × prompt baselines and concentration by suite

This aggregates **all eligible RTC task families within each model and prompt condition**, with each suite given 100 seed opportunities. `Predicted-only` gives the number of unrun suites; their frozen failure predictions are all zero. Rates are hybrid bounds over all eligible suites, so they should be read alongside the task-matched human baselines above rather than as a single human-vs-AI effect across unequal task mixes.

The [derived final summary](../analysis/rtc_factorial_v2_final_summary.json) contains the six model/prompt totals and all 66 suite-level rows so the table and failure concentration can be recomputed from raw originals and frozen forecasts.

| Model | Prompt | Eligible | Measured | Predicted-only | Measured failures | Missing originals | All-eligible rate bound |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | Absent | 4 | 2 | 2 | 0 | 0 | 0% |
| Luna | Present | 3 | 2 | 1 | 0 | 0 | 0% |
| Sol | Absent | 15 | 11 | 4 | 24 | 4 | 1.60–1.87% |
| Sol | Present | 15 | 13 | 2 | 0 | 8 | 0–0.53% |
| Astra | Absent | 15 | 11 | 4 | 13 | 0 | 0.87% |
| Astra | Present | 14 | 11 | 3 | 0 | 0 | 0% |

Relative to each model's absent-prompt baseline, the present-prompt bound implies a **66.7–100% lower** all-eligible rate for Sol and a **100% lower** rate for Astra; Luna's relative change is undefined because both rates are zero. These are arithmetic summaries of the hybrid bounds, not causal effect estimates. Sol's 12 missing originals and both models' prediction-only counting suites limit the interpretation.

Exactly **three of the 50 measured AI suites** account for every observed AI seeded failure; the remaining 47 have zero observed assertion failures (eight of those have at least one missing verdict). Sixteen more suites have only unmeasured 0/100 forecasts.

| Frozen AI suite | Model / prompt | Seeded failures | Evaluable seeds | Missing | 95% Wilson interval on evaluable seeds |
| --- | --- | ---: | ---: | ---: | ---: |
| `sol-range_absent-rtc_alarm_pending-r01` | Sol / absent | 11 | 100 | 0 | 6.25–18.63% |
| `sol-range_absent-rtc_alarm_pending-r03` | Sol / absent | 13 | 100 | 0 | 7.76–20.98% |
| `astra-range_absent-rtc_alarm_pending-r05` | Astra / absent | 13 | 100 | 0 | 7.76–20.98% |

The eight suites with missing original seeds are `sol-range_absent-rtc_alarm_callback-r04` (1), `sol-range_absent-rtc_alarm_pending-r04` (2), `sol-range_absent-rtc_alarm_pending-r05` (1), `sol-range_present-rtc_alarm_callback-r02` (4), `sol-range_present-rtc_alarm_callback-r03` (1), `sol-range_present-rtc_alarm_callback-r04` (1), `sol-range_present-rtc_alarm_pending-r01` (1), and `sol-range_present-rtc_alarm_pending-r05` (1). Their zero observed failures are not complete 0/100 verdicts.

The paired table compares each **measured** AI suite with the upstream selected case at the same seed. Counts are suite–seed pairs, so a human seed is repeated for each measured AI suite in its cell; these are descriptive discordances, not independent trials. The 16 unrun forecasts do not enter this table. `H only` means upstream fail/AI pass; `AI only` means upstream pass/AI fail.

| Task | Model | Prompt | H only | Both fail | AI only | Both pass | AI missing |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Callback | Sol | Absent | 129 | 0 | 0 | 370 | 1 |
| Callback | Sol | Present | 129 | 0 | 0 | 365 | 6 |
| Callback | Astra | Absent | 130 | 0 | 0 | 370 | 0 |
| Callback | Astra | Present | 104 | 0 | 0 | 296 | 0 |
| Counting | Luna | Absent | 34 | 0 | 0 | 166 | 0 |
| Counting | Luna | Present | 34 | 0 | 0 | 166 | 0 |
| Counting | Sol | Absent | 17 | 0 | 0 | 83 | 0 |
| Counting | Sol | Present | 51 | 0 | 0 | 249 | 0 |
| Counting | Astra | Absent | 17 | 0 | 0 | 83 | 0 |
| Counting | Astra | Present | 34 | 0 | 0 | 166 | 0 |
| Pending | Sol | Absent | 104 | 24 | 0 | 369 | 3 |
| Pending | Sol | Present | 129 | 0 | 0 | 369 | 2 |
| Pending | Astra | Absent | 117 | 13 | 0 | 370 | 0 |
| Pending | Astra | Present | 130 | 0 | 0 | 370 | 0 |

All 37 observed AI failures co-occurred with an upstream failure at that seed, and no AI-only failure occurred among evaluable pairs. This relation follows the shared slow-clock boundary and does not imply the AI tests have stronger functional or fault-detection power; that separate quality question awaits the proposed nominal timing mutants.

## Preregistered prompt-context contrasts

The primary contrast is `range-present rate − range-absent rate` in each model × task, then an equal-task average within model and an equal-model average pooled. Negative means fewer failures with the range paragraph. Missing original verdicts propagate to contrast bounds rather than being coded as passes.

| Model | Callback contrast | Counting contrast | Pending contrast | Equal-task contrast |
| --- | ---: | ---: | ---: | ---: |
| Luna | Not eligible | 0 pp | Not eligible | 0 pp |
| Sol | −0.2 to +1.2 pp | 0 pp | −5.4 to −4.4 pp | **−1.87 to −1.07 pp** |
| Astra | 0 pp | 0 pp | −2.6 pp | **−0.87 pp** |
| Equal-model pooled | — | — | — | **−0.91 to −0.64 pp** |

The suite-weighted all-eligible sensitivity view is **37 failures plus four missing / 3,400 absent opportunities** versus **zero failures plus eight missing / 3,200 present opportunities**: a present-minus-absent bound of **−1.21 to −0.84 percentage points**. This weights suite and task mix differently from the registered primary contrast. A measured-only view excludes 16 unrun suites: the three failing pending cells are unchanged because every pending suite was measured; measured counting cells contain zero failures but fewer suites (Luna 2/2, Sol 1/3, Astra 1/2 measured absent/present). No prediction-only suite contributes a positive failure numerator. No complete-data point estimate or empirical Wilson interval is assigned to hybrid cells with missing verdicts or to the 16 forecasts.

For the registered descriptive model comparison on the **three tasks shared by Sol and Astra**, equal-task rates are Sol **1.60–1.87%** versus Astra **0.87%** without range context, and Sol **0–0.53%** versus Astra **0%** with range context. Thus Sol-minus-Astra is **+0.73 to +1.00 pp** absent and **0 to +0.53 pp** present. The difference is driven by the pending task; callback and counting have no observed assertion failures. Luna has only eligible counting suites and is 0% in both prompts, so an all-task Luna comparison would confound model with eligibility. No formal pairwise significance tests or Holm-adjusted claims are made with these three correlated task clusters.

These are descriptive comparisons over three related tasks on one board/driver/emulator. The range-present prompt also included a generic reminder that oscillator tolerance does not bound ISR-to-thread delivery; its effect cannot be isolated from the numeric range. Luna has eligible counting suites only. Suites and seeds are repeated observations within task, so a large per-seed denominator is not independent task replication; task-cluster-aware inferential claims would be exploratory with three correlated clusters. The 16 unrun forecasts and 12 Sol missing verdicts further limit causal interpretation.

## Predictability and other timing assumptions

The frozen source review found 30 clock-only predictable and 36 not-predictable among 66 functionally eligible RTC suites. The latter were all measured. The categories below refine the original reasons **after execution began**; they are descriptive source labels, not failure causes or preregistered context endpoints. The [36-row ledger](../analysis/rtc_threshold_sample_v2/not_predictable_categories.csv) records each suite and original reason.

| Model | Prompt | Eligible | Predictable | Not predictable | Callback delivery/order | Pending polling/service | Multistage flow |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | Absent | 4 | 4 | 0 | 0 | 0 | 0 |
| Luna | Present | 3 | 3 | 0 | 0 | 0 | 0 |
| Sol | Absent | 15 | 7 | 8 | 5 | 3 | 0 |
| Sol | Present | 15 | 5 | 10 | 5 | 4 | 1 |
| Astra | Absent | 15 | 6 | 9 | 5 | 4 | 0 |
| Astra | Present | 14 | 5 | 9 | 4 | 4 | 1 |

The separate [latency-assumption source review](FACTORIAL_LATENCY_ASSUMPTIONS.md) found 28 definite, 24 unknown, and 14 not found among these 66 eligible RTC sources. Clock-rate perturbation does not directly test callback delivery latency or an unsupported immediate `K_NO_WAIT` check. A suite with 0/100 clock failures may still have that assumption. Static [padding and wait-style results](RTC_STATIC_PADDING_AND_WAITS.md) and the [upstream source scan](UPSTREAM_STATIC_THRESHOLD_SCAN.md) are separate source-only observations, not additional simulation outcomes.

The source-only quality inventory gives a more specific reading of the 0-failure suites. A ten-RTC-second transition needs 18.823529 host seconds at the legal 17-kHz endpoint in the ideal model. Of 66 eligible suites, **three have a scalar budget below that value** (the three failing pending suites), **15 have 1–2× that budget**, **12 have more than 2×**, and **36 cannot be reduced to one clock-only budget**. The `>2×` threshold is descriptive over-padding, not proof of weak assertions. The syntax inventory finds fixed-sleep calls in 57/66 and event-wait API calls in 13/66; the categories overlap, and `K_NO_WAIT` is not a blocking wait. Median nominal wall runtime by model/prompt is about 38–41 seconds per suite in the saved logs. The 390-source [latency review](FACTORIAL_LATENCY_ASSUMPTIONS.md) and 66-suite RTC subset retain `unknown` labels rather than declaring them safe. These static data distinguish some clock margins and non-clock premises, but only the approved fault tests can assess whether the surviving suites detect early, late, and absent behavior.

Among the **47 measured AI suites with zero observed clock-rate assertion failures**, six are statically over-padded, five have a scalar budget at or below 2× the ideal slow-bound transition, and 36 have no defensible scalar clock-only budget. Separately, **21/47 have a definite latency/ordering assumption**, 23 remain unknown, and only three have no such source pattern found. These categories overlap. Thus the zero-failure group is a mixture of long waits, behavior that clock-rate alone cannot predict, and unresolved timing premises; it cannot yet be called well written or mutation-strong. The three failing suites have below-bound scalar budgets and no separately established non-clock latency premise. Of 16 prediction-only suites, six are over-padded and seven have a definite latency premise, but none has measured varied-timing outcomes.

| Model | Prompt | Over-padded / scalar-assessable | Fixed-sleep syntax | Event-wait syntax | Definite latency premise | Latency unknown | Nominal wall median per suite |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | Absent | 0/4 | 4/4 | 0/4 | 2/4 | 1/4 | 38.19 s |
| Luna | Present | 3/3 | 3/3 | 0/3 | 2/3 | 0/3 | 40.74 s |
| Sol | Absent | 2/7 | 15/15 | 1/15 | 8/15 | 3/15 | 38.08 s |
| Sol | Present | 2/5 | 13/15 | 5/15 | 3/15 | 9/15 | 37.91 s |
| Astra | Absent | 5/6 | 10/15 | 5/15 | 8/15 | 5/15 | 38.19 s |
| Astra | Present | 0/5 | 12/14 | 2/14 | 5/14 | 6/14 | 38.52 s |

The over-padding denominator excludes suites without a scalar clock-only budget. Wait styles are syntactic and can overlap; nominal times are medians of saved per-suite pass medians. Latency categories are post-start descriptive source coding, with `unknown` retained. The [row-level padding](../analysis/rtc_padding_audit.csv), [wait/runtime](../analysis/rtc_static_waits.csv), and [latency](../analysis/factorial_latency_assumptions.csv) files preserve each source judgment.

## Reproduce and next review gate

From the repository root, run `python3 analysis/rtc_factorial_v2_final_audit.py` to verify raw coverage, locks, sampled vectors, replays, and classifications and regenerate the derived JSON. Run `python3 analysis/rtc_factorial_v2_summary.py` for per-suite Wilson intervals and cell counts. Raw original and replay records remain under `results/rtc_factorial_v2`; no records were rewritten.

### Approved reduced reference result and quality-arm status

The separately built reference tests passed **3/3 nominal controls, 6/6 legal endpoint challenges, and 69/69 selected failed-seed challenges**. The seed unions were 26 callback, 17 counting, and 26 pending. The [reference audit and before/after ledger](../analysis/rtc_reference_triage_classification.json) therefore retains **112/112 brittle-test classifications**; no flip changed category. The reference provides simulation triangulation, not a physical-hardware oracle. Its 75 challenges consumed **50.9 summed process wall minutes** and about **18 minutes from first to last completion** with three workers. The first nominal attempts under a restricted sandbox crashed at virtual zero; their raw records are preserved separately from the successful access-retry series. See the [reference result](RTC_REFERENCE_TRIAGE_RESULT.md) and [registered manifest](../results/rtc_reference_triage_access/manifest.json).

The [timing-mutant activation audit](../results/rtc_timing_mutants/activation_audit.json) confirms that the 64-kHz early and 10-kHz late RTC variants trigger the intended reference assertions for all three tasks. The registered 1-Hz nonfiring variant crashed Renode with divide-by-zero before virtual time advanced, so it is **invalid and scores no test kills**. The [three-fault quality report](RTC_MUTATION_QUALITY_REPORT.md) audits 138 early/late and 69 replacement nonarrival suite runs: **0/69 early kills**, **52/69 late kills** (49/66 AI and 3/3 upstream), and **68/68 evaluable nonarrival kills** (65/65 AI and 3/3 upstream). One additional nonarrival original is a startup harness error and remains unevaluable. The replacement fault activated on all three references and uses a separate driver build at nominal RTC frequency. The source-only [padding/wait inventory](RTC_STATIC_PADDING_AND_WAITS.md), [33-file upstream threshold scan](UPSTREAM_STATIC_THRESHOLD_SCAN.md), and [latency review](FACTORIAL_LATENCY_ASSUMPTIONS.md) are complete. The [dated amendment log and exact generation setup](../paper/DESIGN.md) remain the analysis provenance. The [delivery-delay pilot feasibility report](RTC_LATENCY_PILOT_RESULT.md) records 136 successful builds but **zero pilot suite verdict runs**, because the mandatory one-tick reference smoke changed two-alarm delivery. The HSI factorial arm has not started.
