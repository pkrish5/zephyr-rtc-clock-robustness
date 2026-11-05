# Study design (working document)

## 2026-10-07 proposed firmware-offset quality arm; pending review

The manuscript review requested driver faults that set an alarm one RTC calendar second early and late at nominal clock, to distinguish alarm-programming oracle strength from detection of a globally out-of-spec oscillator. The [operator and scoring proposal](../notes/RTC_FIRMWARE_ALARM_OFFSET_PROPOSAL.md) is **not approved or run**. It proposes two separate, date-normalized driver variants, reference activation before suite scoring, and 138 suite challenges over all 69 eligible suites. Forty-one callback/pending suites can activate an alarm fault; 28 calendar-counting suites are non-activation controls and must not be included in alarm-fault kill denominators. Existing legal-clock and mutation raw records remain unchanged. The estimated execution is 1.5–3 hours wall time after implementation, plus 1–2 hours engineering. Await user review before builds or runs.

## 2026-10-06 manuscript draft status

The approved workshop outline was developed into `paper/draft/main.tex` and `paper/draft/refs.bib` using ACM `sigconf`. The draft separates legal-clock measurements, prospectively frozen predictions, missing original verdicts, reference triage, out-of-range mutation challenges, and single-rater source coding. It reports the historical HSI null and the 33-file static scan as distinct evidence. No schedule, source eligibility, raw result, or prediction lock was changed for manuscript preparation. The title and claims are bounded to selected Zephyr RTC tests and the current simulator configuration. The target is about eight pages plus references; final layout and wording remain for user review.

Updated: 2026-10-07 UTC. Phase 0 is a mechanism check; it cannot answer RQ1–RQ3. The selected RTC and 100-MIPS HSI historical arms are complete. The 13-task historical Luna comparison is frozen; the balanced three-model/two-context factorial below was registered before any Sol or Astra generation. Its generation, gates, and approved v2 RTC arm are complete. The reduced reference triage and three-fault mutation quality score are complete, with one unevaluable nonarrival startup error. The exploratory latency pilot stopped at its one-tick reference feasibility gate before suite verdict runs and is deferred to future work. The HSI factorial arm remains deferred.

## Dated quality cross-tab and latency disposition — 2026-10-07 UTC

The [quality report](../notes/RTC_MUTATION_QUALITY_REPORT.md) now reports per-mutant kill counts and 95% Wilson intervals by model × prompt condition, including the three upstream controls, and the share of suites killing both early and late faults. Source-only wait-style and padding strata are cross-tabulated with those kills; the [derived audit](../analysis/rtc_quality_cross_tabs.json) retains exact counts and intervals. The 47 measured AI suites with zero legal-clock assertion failures contain 21 definite non-clock latency premises, 23 source-unknown cases, and three with no such premise found. Their absent/present prompt split is 12/9 definite and 9/14 unknown, respectively. These are post-start descriptive labels, not preregistered prompt-effect estimates.

**Interpretation correction, 2026-10-07:** These latency counts do not support a general claim that tolerance context substitutes clock-rate assumptions with latency assumptions. The historical bound-context supplement `r05` remains one illustrative immediate second-callback `K_NO_WAIT` case outside the factorial sample; it is not evidence for a cohort-level shift.

The approved pilot's one-tick ISR busy wait logged one achieved ~1-second delay but did not deliver both alarm callbacks to the two-alarm reference before its 26-second ceiling. The cause among injection, Renode, and firmware interaction remains unknown. A workqueue or model-level delivery hook would change the mechanism and need fresh implementation and reference validation; no such single alternative is demonstrated within a one-hour budget. **Defer dynamic latency injection to future work**, with zero pilot suite verdict runs and no pilot effect estimate. The paper may use the static latency-assumption categories with their unknowns and explicit limits.

## Dated nonarrival completion and recovery provenance — 2026-10-07 UTC

The approved driver-path nonarrival fault activated on all three task-specific references. Its 69-suite scoring was interrupted after 32 original suite records (31 assertion failures and one startup `harness_error`) and three open monitor/UART artifacts without verdict records. The frozen runner refused to overwrite partial results. The [append-only recovery registration](../results/rtc_nonarrival_driver_v3_resume/manifest.json) locked the 37 missing suite IDs, hashes of the three interrupted artifacts, original manifest/runner/source/driver/platform settings, and three disjoint workers before any recovery run. It reused verified original builds and saved verdicts in a separate namespace. The [audited score ledger](../analysis/rtc_quality_mutant_scores/rows.csv) now includes all 69 planned nonarrival records: 68 explicit kills and one original virtual-zero harness error, kept unevaluable. The [quality report](../notes/RTC_MUTATION_QUALITY_REPORT.md) presents the early/late/nonarrival scores by model and prompt condition. This completion record does not change legal LSI schedules, frozen binaries, forecasts, or RQ2 denominators.

## Dated reduced-follow-up execution decision — 2026-10-06

The user approved the three reference oracles at legal endpoints and every observed failing seed, the static padding/wait/upstream-scan analyses, three nominal-host RTC fault operators per task, documentation, and the distinct latency-assumption source category. Priority is test quality, wait style/runtime, and latency coding. The optional delivery-delay pilot remains on hold until the source counts are reviewed. The [RTC v2 final report](../notes/RTC_FACTORIAL_V2_FINAL_REPORT.md) now adds model × prompt baseline rates and the three-suite concentration of all 37 observed AI seeded failures.

Before execution, the reduced proposal estimated **25–60 minutes wall time** for 75 reference challenges and **1.5–3 hours wall time plus operator engineering** for 207 mutant test executions. The three reference sources built and passed nominal plus both legal endpoints. The first three nominal attempts remain recorded as virtual-zero Renode crashes from sandbox-denied monitor history; a separately registered access-retry namespace uses the same frozen ELFs. The 69 failed-seed reference challenges all passed there. The [before/after triage](../notes/RTC_REFERENCE_TRIAGE_RESULT.md) retained all 112 source-backed brittle-test classifications. The timing-mutant manifest fixes nominal CPU/SysTick, original test ELFs, three out-of-range effective RTC clocks, and a 70-virtual-second observation cap. Early and late reference activations reached their intended assertions in all three task families. The `never` 1-Hz variant crashed Renode with divide-by-zero before a verdict and is **invalid**. Under the approved proposal's fallback rule, no test suite is scored against a replacement operator without user review. The original activation record remains visible; a replacement choice was requested. No latency-injection pilot has begun.

## Dated RTC v2 completion — 2026-10-06: review stop

The three workers finished the unchanged registered schedule: all 53 measured suites have 100 seeded originals and two endpoint originals (**5,406/5,406**). Fourteen sampled predictable suites matched every frozen per-seed forecast with no missing verdict. Sixteen unsampled predictable suites remain prediction-only. Original seeded outcomes were 5,182 pass, 106 assertion fail, and 12 harness error; all 112 seeded-plus-endpoint assertion failures replayed with identical persisted trace fields and have source-backed `brittle_test_assumption` entries in the separate classification ledger. The 12 harness errors stay missing. The [final audited report](../notes/RTC_FACTORIAL_V2_FINAL_REPORT.md) presents the per-task upstream rates, 66-suite hybrid cell bounds, preregistered contrasts, and not-predictable source categories. No prediction mismatch occurred. This is a result report, not an amendment to the frozen forecast or eligibility rules. Stop for review before the separately proposed reference, mutation, latency-delay, or HSI work.

## Dated latency-dimension amendment — 2026-10-05: source coding complete, pilot proposed

The user added a distinct source-review category, **`latency assumption, not exposed by clock-rate perturbation`**, for unsupported asynchronous delivery/observation windows such as an immediate `K_NO_WAIT` check after a callback. This phrase names a timing dimension that **clock-rate variation alone cannot reliably test**; it does not assert that clock variation could never happen to expose a given source. The [post-start, 390-row recoding](../analysis/factorial_latency_assumptions.csv) uses the frozen source-review evidence and source hashes, preserving the earlier functional and timing-bound labels. The [category report](../notes/FACTORIAL_LATENCY_ASSUMPTIONS.md) provides counts by model × prompt condition for all generated sources and separately for the 66 eligible RTC suites; unresolved source judgments remain `unknown`. This category is descriptive after v2 execution began, not a preregistered model-effect endpoint. A suite with 0/100 clock-induced failures may still have it; the completed `astra-range_absent-rtc_alarm_callback-r01` is a concrete example. The historical bound-context `K_NO_WAIT` supplement remains outside factorial denominators.

**Historical proposal, superseded by the 2026-10-06 approved pilot and 2026-10-07 deferral:** An [optional seven-source pilot](../notes/RTC_LATENCY_PILOT_PROPOSAL.md) was proposed: one flagged eligible RTC suite per model × prompt cell plus the excluded supplement as a positive control. At nominal 32-kHz LSI, use an isolated STM32 RTC driver variant to delay callback delivery or the first post-set calendar read by **one RTC calendar tick (1 s), 1 ms, or 10 ms**. These are exploratory plausible magnitudes, **not datasheet-proven legal delivery bounds**, and the driver hook must demonstrate its achieved delay before any suite outcome is interpreted. The pilot is purposive and separate from RQ2 legal-schedule rates. The original estimate was 18 factorial plus three control nominal runs, roughly **20–30 serial machine-minutes or 15–30 wall minutes**, plus up to **two engineering hours** for the isolated hook and feasibility check. No dynamic suite verdict followed this proposal.

## Dated reduced follow-up amendment — 2026-10-05: proposal, execution pending approval

The user's revised request supersedes earlier broader reference-oracle and test-quality proposals where they differ, without changing the running v2 arm, its locks, forecasts, raw records, or original classifications. **Keep v2 running. Start no new simulation or mutation run until it completes and the user approves the estimated work.** The [reduced proposal](../notes/RTC_REDUCED_FOLLOWUP_PROPOSAL.md) fixes the intended cases, triage rule, mutant scoring, analysis limits, and preapproval runtime estimates.

For each RTC task, use one separately hashed, spec-derived reference ztest with an observable event/state wait, early-firing check, and explicit worst-case-plus-margin ceiling. Run the three references only at the two legal LSI endpoints and at each distinct **observed failing seed within that task** across measured AI and upstream tests. Replay reference failures and apply the four-way triage to every original RTC flip; report classification changes and preserve unknowns. The reference is a diagnostic triangulation, not an independent hardware proof. The drafted sources are in [`subjects/reference_rtc`](../subjects/reference_rtc); they are uncompiled as of this entry.

For test quality, report static clock-window padding ratio and over-padding (`>2×` the ideal slow-endpoint ten-RTC-second transition) per model × prompt, keeping non-scalar cases unknown. Use three activated timing fault operators per task—never fires, later than the legal maximum, earlier than the legal minimum—at nominal clock against all 66 eligible AI suites and all three selected upstream tests. This requires 207 planned test-mutant executions. Fault operators intentionally violate normal hardware behavior and belong to a separately labeled quality arm, not RQ2's legal schedule denominator. Require activated-mutant evidence before crediting kills; retain invalid and unevaluable cases. Extract wait styles and nominal wall times from frozen source and existing logs only. Scan all upstream Zephyr test sources under the named RTC, counter, and timer trees statically, leaving unknown hardware-bound cases unresolved. The [static wait table](../analysis/rtc_static_waits.csv), [padding ledger](../analysis/rtc_padding_audit.csv), and [upstream scan](../analysis/upstream_timing_threshold_scan.csv) are dated, auditable, source-only outputs.

**Analysis unit and clustering:** the task is the primary comparative cluster. Five independently generated suites within a model × prompt × task cell and 100 paired schedule seeds within a suite are repeated observations, not independent firmware subjects. Give task-specific descriptive rates first. For any pooled model/context comparison, aggregate task-level contrasts with equal task weight, show suite-weighted sensitivity, and use task-cluster-aware uncertainty; with only three correlated RTC tasks sharing STM32F407/Zephyr/Renode, intervals and inference are exploratory. Wilson intervals are for within-suite seed proportions, not cross-task model effects. Missing/harness errors and prediction-only outcomes remain separate.

**Context limitation:** the range-present prompt includes both a documented tolerance range and a warning that the clock bound alone gives no ISR-to-thread latency guarantee. A context effect cannot be separated from a generic timing-reminder effect in this factorial. A reminder-only prompt control is future work.

### Amendment log and generation provenance

| Date (UTC) | Decision | Relation to present work |
|---|---|---|
| 2026-09-29 | Split functional adequacy (eligibility) from timing-bound adequacy (outcome) | Retrospective on historical Luna; both original strict and amended filters retained. |
| 2026-09-29/30 | Freeze 13-task cross-model set after RTC qualification; exclude IWDG | Defines three correlated RTC task families and ten HSI tasks. |
| 2026-10-03 | Approve and lock three-model × two-context generation | Prospective before the 390 calls; exact prompt bytes and random order saved. |
| 2026-10-04 | Replace full RTC scan with clock forecast plus sampled validation; defer HSI | Supersedes 113-hour full RTC plan. |
| 2026-10-04 | Balance v2 predictable sample and use hybrid all-eligible contrast | Supersedes v1 sample only; 14 predictable sampled, 36 non-predictable full, 16 prediction-only. |
| 2026-10-04 | Approve v2 RTC execution and matched upstream tests | Completed with three workers and identical registered seed frequencies. |
| 2026-10-05 | Reduce reference triage and quality arm, add static analyses | Post-start proposal; **no new runs before completion and approval**. |
| 2026-10-05 | Add a separate latency-assumption source category and optional delay pilot | Post-start descriptive recoding; pilot awaits completion and approval. |
| 2026-10-06 | Complete and audit v2 RTC arm | Results only; no change to locks, raw records, or pending approval gate. |
| 2026-10-06 | Approve reduced reference/quality/static additions; hold latency injection | Reference triage executing; invalid `never` mutant awaits replacement decision. |
| 2026-10-06 | Approve interim two-fault scores, driver-path nonarrival replacement, and sampled latency pilot | References for the replacement must activate before scoring; 34 pilot suites × four levels are separate from legal-clock rates. |
| 2026-10-06 | Stop latency pilot at failed one-tick mechanism smoke | One of two expected callback deliveries was absent before the reference ceiling; 136 builds, zero suite verdict runs, cause unknown. |
| 2026-10-07 | Complete append-only nonarrival scoring; report mutant/source cross-tabs | 68/68 evaluable nonarrival kills, one startup error; Wilson intervals and task-clustering limits retained. |
| 2026-10-07 | Defer dynamic latency pilot to future work | No validated replacement hook within one-hour budget; static definite/unknown source categories remain descriptive. |

The exact generation lock is [`generated/spec_context_factorial_v1/lock.json`](../generated/spec_context_factorial_v1/lock.json), with [call order](../generated/spec_context_factorial_v1/call_order.json) and [protocol](../generated/spec_context_factorial_v1/PROTOCOL.md): 13 frozen task specifications × requested model IDs `gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra` × `range_absent`/`range_present` × five fresh complete C ztest sources = **390 intended and saved calls**. Within each task the absent prompt is the unchanged base rendering; the present prompt adds the frozen HSI/LSI paragraph immediately before the output instruction. Exact per-task/condition prompt bytes and SHA-256 values, schema, build settings, board, and source hashes are in the lock/metadata. The order was interleaved with Python `random.Random(20261003).shuffle`; each call used direct-argument prompt transport, read-only/no-tool instruction, and `codex-cli 0.158.0-alpha.2.1`. Metadata dates span **2026-10-03 19:02:39 to 2026-10-04 02:03:20 UTC**, with individual attempts, tokens, outputs, and source hashes saved. The event logs report the requested model identifiers but **no finer backend model version or snapshot** (`model_reported_by_events` is empty for all 390); do not invent one. Billed-dollar cost is unavailable in the authenticated CLI and is recorded unknown, not zero. The earlier Sol feasibility sample, historical Luna sources, and context supplement are excluded from factorial denominators.

## Dated RTC execution amendment — 2026-10-04: approved v2 arm

The user approved the v2 sample lock and its hybrid all-eligible contrast. Treat **predictability itself as a reported source-review outcome**: publish, by each model × prompt condition, the counts of clock-only predictable and not-predictable functionally eligible RTC suites; list every not-predictable suite ID with its frozen reason from the forecast ledger. This label describes whether the registered LSI rate alone determines a defensible pass/fail vector. It is not a robustness verdict and must not be inferred from the varied runs. Preserve the 66-suite denominator and the task-family breakdown.

Run the three matched repository-maintained RTC selected cases (alarm callback, calendar counting, alarm pending) in full over the **same locked 100 seed-frequency schedule and both endpoint challenges** as the 50 measured AI suites. Show each task's human seeded failure rate, missing/harness-error count, and Wilson interval beside every available model × prompt × task-family AI rate. The upstream cases use their separately qualified frozen ELFs and selected-case verdicts; do not treat them as interchangeable with all cases in the upstream rtc_api suite. Earlier selected-case RTC runs are historical evidence, not substitutes for this contemporaneous baseline.

Use three concurrent fresh Renode processes on this host's ten reported logical CPUs, leaving headroom for the monitor, filesystem, and interactive work. Assign whole suites to workers, with each suite's seeds 0–99 and endpoints processed by only one worker; keep separate, exclusive-create record/UART/monitor/trace files for every suite–seed. The same seed *values* must occur in each suite to retain pairing; “no shared seed ranges” means no overlapping suite–seed assignments or shared output files. Record the exact worker allocation, maximum concurrency, host core report, runner hash, and run manifest before starting. Prioritize the 14 sampled predictable suites for early validation, then the 36 not-predictable suites; upstream baselines may run alongside the validation stage. Exact replay and four-way classification begin as observed failures complete. Stop new launches immediately on any sampled evaluable per-seed prediction mismatch and report it for review; a sampled harness error makes validation inconclusive and remains missing rather than being replaced by replay. If all measured results agree, stop for user review at arm completion. HSI remains deferred.

**Dated analysis addendum, 2026-10-04, after execution began:** The final RTC report will also summarize frozen `not_predictable` reasons by model × prompt condition, with an auditable row for each suite. A finer descriptive category coding separates callback delivery/order, pending polling or peripheral service, and explicit multi-stage calendar/delivery control flow. This subcoding is post-start, does not alter the 36 frozen predictability labels or sample, and cannot be treated as a preregistered context effect. The [category report](../notes/RTC_FACTORIAL_V2_REASON_CATEGORIES.md) and [row ledger](../analysis/rtc_threshold_sample_v2/not_predictable_categories.csv) retain this provenance.

## Dated RTC sampling amendment — 2026-10-04: balance prompt conditions and preregister context contrast

This amendment **supersedes only the 12-suite RTC validation sample** in the preceding section, preserving its 66-suite forecast and all older locks/raw data. The user's spec-context comparison needs balanced measurement across range-absent and range-present prompts within each model. The [v2 sample lock](../analysis/rtc_threshold_sample_v2/lock.json) fixes a new seeded, 14-suite predictable sample: Luna 2 absent/2 present, Sol 3/3, and Astra 2/2. It certainty-includes the same three nonzero clock-threshold predictions, then draws one seeded-random suite from every uncovered model × prompt × family stratum and fills the stated quotas using `random.Random(20261004)` on sorted IDs. All eight predictable strata are represented. The 36 `not_predictable` suites still run in full. Thus **50/66 suites** are scheduled for measurement (5,000 registered seeds plus 100 endpoints) and **16/66** remain prediction-only, all forecast at 0/100. The earlier v1 sample remains an immutable, superseded design record. The new base runtime estimate is **about 86 serial machine-hours**, or 29 hours at ideal three-worker scaling, before replay, host contention, and selected upstream state baselines.

The user selected a **hybrid all-eligible primary comparison** because the 36 `not_predictable` suites have no defensible clock-only prediction. Define one verdict for every suite `i` and registered seed `s`: use the **original measured verdict** for the 50 scheduled suites and the **frozen clock-only prediction** for each of the 16 unrun suites. Never substitute a diagnostic replay for an original run. For each model `m`, prompt condition `c`, and RTC task family `t` with eligible suites, report `R(m,c,t) = sum(failure verdicts)/(100 × number of eligible suites in that cell)`. Report the observed and prediction-only contributions to every numerator separately. A measured harness error leaves that seed missing; report lower/upper bounds by assigning every missing verdict pass/fail, and do not present a complete-data point rate for that cell. Predictions have no empirical Wilson interval; measured per-suite rates retain their Wilson intervals and harness-error counts.

**Primary spec-context contrast, preregistered before varied runs:** within each model and each RTC family represented under both prompts, compute `Δ(m,t) = R(m,range_present,t) − R(m,range_absent,t)`. Compute each model's `Δ(m)` as the equal-family average of its available `Δ(m,t)` values (Luna counting only; Sol and Astra callback, counting, pending). Compute the pooled `Δ` as the equal-model average of Luna, Sol, and Astra `Δ(m)`. Negative values indicate a lower hybrid failure rate when the documented range was in context. This uses **all 66 functionally eligible RTC suites** while avoiding domination by a model or task family with more eligible generations. Also show each family contrast, raw condition numerators/denominators, a suite-weighted pooled sensitivity view, and a measured-only comparison. The design is descriptive: the 16 imputed predictions and unequal task mix, especially Luna's absence of eligible callback/pending suites, preclude treating the pooled difference as a direct experimental flip-rate effect.

The all-eligible hybrid contrast is **conditional on the prospective exact-vector validation criterion for all 14 sampled predictable suites**. If any evaluable seed disagrees with its frozen prediction, or a harness error leaves the 100-seed vector unverified, do not label the hybrid result validated: publish the measured results, discrepancy/inconclusive ledger, and seek user review on sample expansion or model revision. Do not silently recalculate predictions after seeing outcomes. Even exact 14/14 agreement does not make the 16 unrun suite outcomes measured; publish them in a separate prediction-only table. HSI remains deferred. **No RTC or HSI factorial varied run begins before user approval.**

## Dated pre-Phase-3 amendment — 2026-10-04: RTC threshold validation sample and HSI deferral

**Status: proposed execution plan, frozen before any new factorial varied-timing run; user approval required before execution.** This amendment supersedes the earlier instruction to run all 66 functionally eligible factorial RTC/LSI suites across all 100 seeds. That full arm was estimated at about **113 serial machine-hours before replays**. The already completed selected RTC callback arm found no evaluable mismatch between its registered clock-boundary calculations and seeded verdicts: 26 predicted/observed upstream failures, 13/13 in primary Luna, and 0/0 in the separate supplement. Those are three selected suites, not proof that clock-only prediction works for new tests. A prospective sampled validation directly tests whether that threshold method transfers across the new cohort while reducing simulation cost. Preserve the old full-arm registration and historical raw data as superseded records; do not edit them.

The [frozen prediction ledger and sample lock](../analysis/rtc_threshold_sample_v1/lock.json) commit the 66 eligible suite IDs, source and ELF hashes, original 100-seed LSI frequencies, prediction status, predicted per-seed verdicts and failure counts when possible, model assumptions, and sample selection before any new varied run. The clock-only hypothesis uses the fixed 128×250 RTC prescaler: ten calendar seconds require `320000/f_LSI` host seconds. A documented source observation budget `B` predicts failure when this exceeds `B`. Such predictions are **model hypotheses**, not observed flip rates or silicon guarantees; ordinary thread/poll service and Renode RTC model behavior are assumptions to be tested. The 27 calendar-counting sources and three short-deadline alarm-pending sources yield 30 predictions: 27 at 0/100, one at 11/100, and two at 13/100. The remaining 36 are `not_predictable`: 19 callback suites depend on delivery/order or callback-state latency and 17 pending suites have non-decisive or multiple observation phases. `K_NO_WAIT`-style delivery premises cannot be inferred from LSI rate. The [66-row table](../analysis/rtc_threshold_sample_v1/forecast_table.csv) exposes each classification and its source expression; the locked JSON is authoritative.

Use Python `random.Random(20261004)` on sorted IDs. Certainty-include all three nonzero-prediction suites, choose one seeded-random suite from each still-uncovered model × prompt-condition × task-family stratum among predictable suites, then fill without replacement to **12 predictable suites**. The [sample manifest](../analysis/rtc_threshold_sample_v1/sample.json) freezes the exact 12. Run all **36 not-predictable suites in full**, so 48 suites receive the registered 100 seeds and both endpoint challenges (4,800 primary seeded runs plus 96 endpoints); 18 suites remain prediction-only. The sample covers all eight predictable strata; strata without a predictable suite are covered by full runs. The certainty component enriches boundary tests, so unweighted sample averages are not representative estimates. Do not silently substitute predictions for measured outcomes in RQ2 or cross-model comparisons.

**Prospective agreement criterion:** every sampled predictable suite must have 100 evaluable original seeded verdicts, with the **entire 100-seed pass/fail vector exactly equal** to its frozen prediction. Matching counts with different failing seeds is disagreement. A harness error makes that suite's validation inconclusive and remains in raw accounting; diagnose it separately without replacing the original outcome. For any evaluable mismatch, report and exact-replay the suite, apply the four-way cause procedure, investigate source/model/polling assumptions, and propose whether to expand sampling to the user **before** any expansion. Endpoints are separate challenges and do not alter the 100-seed agreement score. Even 12/12 exact agreement would validate only this sample and model, not prove correctness for the 18 unrun suites.

At the prior RTC seeded mean of 60.4 wall seconds per process, the proposed 48-suite scan is about **82 serial machine-hours**, roughly 27 hours with ideal three-worker scaling, before contention, replays, and two RTC state upstream baselines. The 18 unsampled suites' results must be published as **predicted counts only**, in a table separate from observed sample and not-predictable full-run outcomes; they receive no measured flip rate, Wilson interval, or empirical pass claim. The original ten-task 100-MIPS **HSI factorial arm is deferred**, not reinterpreted as robust: the prior arm found zero assertion flips among 4,213 evaluable seeded runs under its narrow ±1% model, with startup errors separately retained. Its locked schedule and eligible inventory remain frozen for a later approval decision. The [proposal and limitations](../notes/RTC_THRESHOLD_SAMPLE_PROPOSAL.md) give the runtime and sample details. **Stop for user approval before any RTC or HSI factorial varied run.**

## Dated factorial amendment and cross-model preregistration — 2026-10-03

The user approved the [2026-10-01 proposal](PROPOSED_SPEC_IN_CONTEXT_AMENDMENT.md) before any Sol/Astra generation. Register **13 fixed tasks × Luna, Sol, Astra × documented timing range absent/present × five independent outputs**, for 390 fresh source-generation calls. The earlier 65 Luna suites remain a historical cohort, not reused as the factorial's no-range Luna cell; the five RTC context-supplement outputs and the one-suite Sol feasibility sample stay excluded. This avoids conflating timing context with generation date, prompt transport, and partly different API hints. The existing 13-task manifest, old locks, prior test binaries, and raw results are not edited. Save exact prompt bytes and SHA-256 hashes for each of 26 task/condition inputs before any new model call, and a randomized, saved interleaved call order. Use the same direct-argument CLI transport, JSON schema, build configuration, and output handling in every new factorial cell. Record requested/reported model ID, CLI version, UTC date, raw response/events, tokens, failed attempts, and source hash; billed cost is unavailable unless the tool reports it.

The range-present prompt adds only the cited input bound and qualifier: STM32F407 HSI 16 MHz ±1% at 25 °C for HSI tasks, or STM32F407 LSI 17–47 kHz at 3 V over −40 to 105 °C and the fixed RTC prescaler 128×250 for RTC tasks. It states that an oscillator bound alone is not an ISR-to-thread delivery-latency guarantee. The absent prompt is the unchanged original rendering. Neither variant includes upstream test source, prior test outcomes, a computed failure boundary, or repair advice. The two prompts within each task differ only in this context paragraph. Keep the source-blind context factor distinct from the earlier exploratory RTC supplement, which also changed API hints.

**Preregistered descriptive contrasts, before outputs exist:** (1) Luna–Sol, Luna–Astra, Sol–Astra separately within each prompt condition; (2) range-present minus range-absent within each model; (3) model × context interaction; and (4) each model/condition against its matched upstream selected case. For each contrast, report all five intended generations per task, build yield, initial nominal pass, original strict oracle adequacy, amended functional adequacy, and timing-bound adequacy; source timing labels retain `unjustified`/`none_found`/`unknown`. The primary timing-flip arm requires build success, **five fresh nominal passes at the relevant Phase 3 configuration**, and functional adequacy, regardless of timing-bound judgment. The strict original gate is a secondary analysis. A condition with no eligible suite has an undefined flip rate, never zero. Each eligible suite will use the identical locked 100-seed 100-MIPS HSI or LSI schedule for its task, with endpoints outside the rate denominator, raw hashes/traces, exact failure replay, and four-way classification. **No new factorial Phase 3 run starts before the user's next review.**

Show task-stratified yields and same-seed paired comparisons; report the ten HSI tasks together but the RTC callback and two correlated RTC state cases separately. Five generations and 100 seeds are repeated measures, not independent firmware subjects. Use paired/task-cluster-aware uncertainty for comparative estimates, Wilson intervals for per-suite seeded flip rates, and Holm correction if testing the three pairwise model contrasts within one context. Keep unknown source judgments and harness-error runs visible. The cross-model causal claim is limited by one board/repository, provider snapshot opacity, model sampling randomness, and the emulator's timing approximation. The [versioned factorial protocol](../generated/spec_context_factorial_v1/PROTOCOL.md) and lock specify the concrete inputs and call order.

### Execution status — 2026-10-04 UTC

The locked 390 calls finalized as 130 frozen sources per model. All 390 have build and source-gate outcomes; 360 built. A first nominal run was saved for each built source, and 336/390 passed it. Five-repeat nominal screens were run only for the 330 built sources labeled functionally adequate; 321/330 passed 5/5. The 30 built but source-inadequate suites were screened once only (12 first-run pass, 17 assertion fail, one timeout), so their 5/5 outcomes are **unmeasured**, not failures. The original strict gate admits 175/390; the amended functional gate admits 321/390, including 105 source-labeled timing-inadequate suites. Source review covers 390/390 and records 330 functionally adequate, 60 inadequate; timing-bound labels are 154 inadequate, 177 no issue found, and 59 unknown. Seven functional labels were corrected in an auditable post-build executable-assertion cross-check before any new varied schedule; timing labels were unchanged. Six nominal virtual-zero harness errors remain non-passes in the original gate records despite separately logged passing diagnostics. The [gate report](../notes/PHASE2_SPEC_CONTEXT_FACTORIAL_REPORT.md) and [prestart reconciliation](../notes/PHASE3_PRESTART_GATE_RECONCILIATION.md) give denominators, trace locations, token counts, and exclusions. **No new factorial Phase 3 varied-timing schedule has run.**

## Dated ordering amendment — 2026-09-29: finalize task set before new model cohorts

The user approved qualifying the existing RTC counting case first and alarm-pending case second, each with its own unchanged-upstream selected-case build, fresh nominal screen, and registered LSI schedule. The user also approved a separate STM32 IWDG reset-state fidelity probe. IWDG enters no corpus or prompt manifest solely from a passing probe: first propose its model evidence and limitations for user review. Both proposed RTC cases read calendar or pending state rather than asserting ISR callback delivery, so retain a separately labeled adjacent LSI stratum and do not fold them into callback-specific prevalence. A user clarification on including these cases in the three-model task list is pending while qualification proceeds.

The 11-task [cross-model lock](../generated/cross_model/lock.json) remains an immutable historical preregistration. It is **superseded before any Sol or Astra comparison call** by this user-requested ordering change. Once the qualifying additions and IWDG decision are resolved, extend the task manifest without editing the original 11-task file, generate and freeze five Luna outputs per new task using the same frozen prompt template and split gates, then lock one complete task list for all three models. Sol and Astra use that same list; exclude the earlier Sol feasibility pilot and keep the RTC bound-context supplement separate. Stop for user review before either new model starts. The new [counting](../subjects/rtc_counting/PROTOCOL.md), [alarm-pending](../subjects/rtc_alarm_pending/PROTOCOL.md), and [IWDG fidelity](../notes/IWDG_FIDELITY_PROTOCOL.md) protocols record this sequence.

The IWDG reset-state fidelity task failed in its original and separately configured variants, so IWDG is excluded from the candidate task set. The two RTC selected cases passed their own 5/5 nominal screens and are the proposed adjacent LSI additions. Two Luna CLI attempts using stdin produced no response; a dated [transport amendment](../generated/luna_rtc_extension/CLI_TRANSPORT_AMENDMENT.md) switched subsequent new-cohort calls to pass the exact same prompt bytes as a CLI argument. This transport difference from the original 55 Luna calls is a disclosed toolchain threat; Sol and Astra will use the new transport if approved.

Expand the RQ1 source packet to about 30 items across tasks, explicitly including uncertain cases. Keep the first reviewer's identity key and labels separate from the user-facing packet; do not disclose those labels before the independent response. Compute kappa only after the user submits complete labels. Let the three registered RTC 100-seed batches finish unchanged, replay and classify every flip, and report the complete paired table before the Step 4 review stop.

## Dated complete-task comparison preregistration — 2026-09-29/30

The [v2 cross-model protocol](../generated/cross_model_v2/PROTOCOL.md) prespecifies the **13-task** comparison before any new Sol or Astra call: the unchanged ten HSI tasks, the original RTC alarm-callback task, and two separately qualified RTC calendar/pending-state tasks. Both new RTC cases use the same STM32F407 RTC, LSI input and Zephyr repository, and neither asserts ISR callback delivery; report them as correlated adjacent timing-source evidence, with the callback case and ten HSI cases distinct. The separate IWDG reset-state probe failed, so it is excluded. The final versioned task manifest and hash lock wait for the ten new Luna sources' build, nominal and source-gate audit; until then this is a **registered design, not a finalized input lock**. The historical 11-task lock remains unchanged and superseded.

**Freeze status, 2026-09-29/30:** The conditional audit completed. The [13-task manifest](../subjects/phase2_tasks_v2.json), [v2 hash lock](../generated/cross_model_v2/lock.json), and [freeze note](../generated/cross_model_v2/FREEZE_STATUS.md) now fix the complete task list before any Sol/Astra call. All 65 saved Luna prompt hashes agree with rendering those task definitions. The new RTC counting Luna outputs had 5/5 builds and 4/5 one-run nominal passes; one failed immediately at `rtc_set_time` because the generated weekday was rejected. All five RTC alarm-pending Luna outputs failed compilation at RTC alarm API signatures. For the ten new outputs, original strict eligibility is **0/10** and amended functional eligibility is **3/10**. Combined with the unchanged initial 55, primary Luna eligibility is **34/65 original strict** and **38/65 amended functional**; the five-suite bound-context supplement remains separate. Source-only timing judgments are preserved for noncompiling suites, and no new RTC-extension timing schedules have been run. These outcomes do not change the locked task list or justify dropping the alarm-pending task.

The completed selected RTC callback arm has seeded flips of **26/98 evaluable** upstream, **13/99** primary Luna r04, and **0/100** in the separate bound-context supplement; three original harness errors remain non-evaluable. All 41 observed seeded/endpoint failures replayed with identical sampled traces and were classified as model-specific brittle test assumptions under the four-way procedure. At 17 kHz the upstream and primary Luna cases fail and the supplement passes; all three pass at 47 kHz. The [100-row paired table and Wilson intervals](../notes/PHASE3_RTC_FINAL_REPORT.md) are the authoritative result. The original strict gate yields no eligible agent RTC comparator, while the amended functional gate includes r04 retrospectively; therefore the lower observed r04 flip fraction is a selected-case outcome, not a model-wide improvement claim. The supplement's `K_NO_WAIT` second-callback premise remains timing-bound inadequate despite its 0/100 flip count.

The three prespecified model contrasts are Luna–Sol, Luna–Astra and Sol–Astra, on matched task-level build/functional yield under both old and amended gates, RQ1 `unjustified`/`none_found`/`unknown` source proportions, and RQ2 functionally eligible flip fractions. Use five frozen outputs per task per model, the same rendered prompt/schema and build/gate rules, the 100-MIPS HSI schedule for ten tasks, and the same fixed 100-frequency LSI schedule for all three RTC cases. Require 5/5 fresh nominal passes before a suite enters a timing-flip numerator. Report per-suite Wilson intervals, paired same-seed disagreements, endpoint challenges outside rates, and unknown/harness errors. Never treat five suites, 100 seeds, or the three correlated RTC cases as independent firmware projects. Any formal three-contrast p-values use Holm correction. The original Luna 55 stdin calls and the ten new Luna direct-argument calls differ in CLI transport after two archived infrastructure failures; the prompt bytes and JSON schema are unchanged, and this possible toolchain confound is disclosed. The old one-sample Sol pilot, connectivity diagnostics, and bound-informed RTC supplement remain excluded from model cohorts.

## Dated study decision — 2026-09-29

The study will evaluate **Luna, Sol, and Astra as separately registered model cohorts under an identical generation, build, oracle-review, and timing-schedule protocol**. Do not pool model cohorts or include the earlier one-sample Sol feasibility pilot in the comparative analysis. Preregister the exact shared prompt, model identifiers and available version metadata, generation count, source context, build and functional gates, schedule list, analysis units, and planned comparisons before starting either new Sol or Astra cohort. The user requires a review stop before those generation calls.

For the HSI schedule arm, use the **100 MIPS nominal CPU setting** so integer `PerformanceInMips` can represent approximately coupled 99–101 MIPS CPU throughput with the documented ±1% HSI/SysTick input range. Screen every candidate again at the new nominal configuration before counting flips. This remains an emulator throughput approximation, not cycle-accurate STM32F407 timing; record the quantization and model-fidelity limits. The already running RTC LSI batches retain their separately locked 16 MIPS protocol and must finish without interruption or reconfiguration.

## Dated protocol amendment — 2026-09-29: separate oracle dimensions

The original Phase 2 oracle gate treated a timing deadline below a legal slow-clock arrival, or an unsupported zero-delay callback-order check, as **overall oracle inadequacy**. That excluded nominally passing tests for the very timing brittleness RQ2 is designed to measure. This amendment was requested **after** primary Luna generation, original oracle review, and the beginning of exploratory RTC Phase 3 runs; it is retrospective for those frozen sources, not a blinded preregistration. Preserve the original decisions and report **both original and amended attrition** without changing any source, ELF, prompt, raw run, or original verdict.

Under the amended gate, score two independent source-review dimensions for every generated suite:

1. **Functional adequacy (filter):** Does an executable assertion meaningfully check the task's intended behavior and reach the relevant firmware path? A source that cannot establish the intended behavior, has a vacuous or wrong assertion, or never checks a required positive/negative property is inadequate or uncertain. A test may be functionally adequate even if its deadline or callback-order premise is wrong. Build success and nominal pass remain separate eligibility gates for pass-to-fail measurements.
2. **Timing-bound adequacy (measured outcome):** Are fixed waits, deadlines, immediate callback checks, and cross-context ordering premises supported by documented hardware bounds or API/synchronization guarantees? Record `supported/no issue found`, `inadequate`, or `unknown`, with source location and justification. This dimension is **not a filter** for the primary timing-flip arm. An absent documented ISR-to-thread latency bound alone is not proof of inadequacy; preserve unknowns.

The primary Phase 3 analysis set is now **frozen suites that build, pass the new nominal screen, and meet functional adequacy**, regardless of timing-bound status. Show a stratified timing outcome for adequate, inadequate, and unknown timing premises, while separately reproducing the original strict-gate result. Noncompiling and nominal-failing outputs stay in the generation denominator. The primary Luna RTC `r04` 15-second cap is a timing-bound issue; its callback/oracle checks must be judged independently for functional adequacy. The bound-informed RTC supplement `r05` tests both callbacks and the calendar state, so its immediate second-callback `K_NO_WAIT` is a **timing-bound adequacy issue, not a functional one**. Its five-sample cohort remains separate from the primary 55 and cannot be pooled into a model comparison. Any recoding after timing outcomes must be marked unblinded, source-backed, and versioned.

The implementation is the [split-gate protocol](../analysis/PHASE2_SPLIT_GATE_PROTOCOL.md), [source decision ledger](../analysis/phase2_split_gate_decisions.json), and [dated reanalysis report](../notes/PHASE2_GATE_AMENDMENT_REPORT.md). The original strict gate yields 34/55 eligible primary Luna suites and 0/5 in the separate RTC supplement; the amended functional gate yields 35/55 and 1/5 respectively. The added primary suite is RTC `r04`, while the supplement `r05` remains a separate context condition. The 34 HSI Luna suites are unchanged by this reanalysis and require the new 100 MIPS nominal screen.

## Historical 11-task preregistration — 2026-09-29: superseded before new model calls

The [cross-model protocol](../generated/cross_model/PROTOCOL.md) and [hash lock](../generated/cross_model/lock.json) fix the shared 11-task manifest, exact prompt/schema, k = 5 independent outputs per task, frozen-source/build/nominal gates, amended functional filter, timing-bound outcome, same-seed schedules, and the Luna/Sol/Astra model IDs. Requested model ID, CLI version, generation date, token usage, and any server model metadata exposed by the CLI must be recorded for each call; exact server snapshots and sampling seeds are unavailable. The prior one-sample Sol feasibility run and the separate RTC bound-context supplement are **outside all three comparative cohorts**. The user will review this lock before any new Sol or Astra call.

The prespecified descriptive contrasts are Luna–Sol, Luna–Astra, and Sol–Astra on matched task-level functional yield, RQ1 timing-assumption rate, and RQ2 flip fraction. Show build/nominal/functional attrition under both the original strict and amended gates; report `unknown` separately. Use per-suite Wilson intervals for 100 seeded schedules, paired same-seed disagreement tables, and task-stratified summaries; the five generations within a task and 100 schedules within a suite are not independent projects. Report the ten HSI tasks separately from the one selected RTC case. Any formal three-contrast p-values require Holm correction. The upstream repository-maintained tests are the matched baseline, with individual human authorship unverified. Luna's split-gate recoding was retrospective and unblinded; do not present it as if preregistered before RTC outcomes.

The [100 MIPS HSI protocol](../subjects/phase3_hsi_100mips/PROTOCOL.md) and [locked input plan](../subjects/phase3_hsi_100mips/plan.json) fix the 100 ±1% oscillator draws and deterministic approximate CPU mapping (99–101 integer MIPS), five fresh nominal screens per version, endpoint challenges outside the denominator, trace/replay rules, and model-limit attribution. Its existing inventory contains 10 upstream cases and 34 Luna HSI suites **before** the new nominal screen. The prior 16 MIPS HSI pilot is separate. Existing RTC batches continue their locked 16 MIPS configuration without interruption. HSI execution waits for those workers to finish to reduce simultaneous Renode load.

The [blinded 12-item RQ1 source packet](../analysis/blind_rq1/PACKET.md) is a purposive matched-task pilot for an independent user label. Authorship fields, source paths, and original comments were removed from the packet; a separate key retains frozen source hashes and the first reviewer's labels. Three-category Cohen's kappa can be computed only after independent labels are returned. Recognizable code style and differing source length still limit blinding. The [additional RTC/IWDG candidate proposal](../notes/ADDITIONAL_SUBJECT_CANDIDATES.md) records model and bound checks; no candidate has been added to the corpus.

## Question and scope

Do agent-written tests of interrupt-driven firmware encode unjustified timing assumptions, and can controlled **legal** timing changes expose those assumptions with firmware and tests frozen? Compare agent and human suites for the same firmware functions. The intended contribution is the **combination** of agent test measurement, hardware-bounded schedule variation, replay, cause classification, human baselines, and repair without weaker oracles.

**Target positioning from the novelty addendum, pending literature verification and the full study:** “The first empirical measurement of timing-assumption brittleness in agent-written tests for interrupt-driven firmware. Holding firmware binaries and tests fixed, we apply legal, deterministic, replayable variations of interrupt arrival and CPU speed in an emulator, classify each verdict flip as (a) brittle test assumption, (b) genuine firmware race, or (c) simulator/peripheral-model artifact, compare agent-written tests against human-written ztest suites, and show targeted repairs remove brittleness without weakening assertions (measured by mutation score).” The earlier hard methodological rule also requires **unknown** as a fourth, explicit outcome; the final claim must preserve that rule. Phase 0 varies the modeled SysTick clock only, so interrupt-arrival and CPU-speed arms remain future work. A priority or “first” claim remains provisional until the full literature check and experiments are complete.

RQ1 measures timing-assumption types in agent and human tests. RQ2 measures verdict flips across seeded legal schedules with frozen artifacts. RQ3 measures whether targeted repairs preserve assertion count, assertion types, and mutation score while removing flips.

## Phase boundaries

0. Feasibility spike: one interrupt-driven firmware, a deliberately authored fixed-sleep test, an event-wait test, 100 nominal trials each, 100 seeded legal-variation trials each, and fresh-process replay. Stop for review.
1. Subject corpus and human baseline, 8–15 subjects. Stop for review.
2. Fixed-prompt repeated agent generation, freezing, static tagging. Stop for review.
3. Schedule experiments and four-way classification. Stop for review.
4. Targeted repairs, mutation checks, and hardware validation sample. Stop for review.

## Phase 0 legal schedule

The STM32F407 datasheet says the reset CPU clock is the 16 MHz HSI RC oscillator and gives HSI accuracy at 25 °C as −1% to +1% ([DS8626 Rev 12, pp. 25 and 105](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf)). The STM32 Cortex-M4 programming manual says `STK_CTRL.CLKSOURCE=1` selects the processor/AHB clock for SysTick ([PM0214 Rev 10, p. 247](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf)). The firmware sets that bit and programs 160,000 ticks, nominally 10 ms. Our allowed frequency range is therefore **15,840,000–16,160,000 Hz**, under the stated 25 °C condition. We do not infer a broader temperature bound from this spike.

Renode's shipped STM32F4 platform defines the NVIC `systickFrequency` constructor parameter ([Renode STM32F4 platform](https://github.com/renode/renode/blob/master/platforms/cpus/stm32f4.repl)). The runner copies that platform and replaces only the SysTick frequency value; it saves and hashes every configured platform. The shipped platform's default 72 MHz is not the reset clock of this bare-metal firmware, so the nominal configuration is 16 MHz. A seed maps to one uniform integer frequency in the allowed range. The firmware ELF and each test file are unchanged between conditions.

The intentionally fragile test advances virtual time 10.05 ms, then asserts that GPIOD pin 12 is high. The robust test samples that same GPIO state every 1 ms until it becomes high or a 12 ms deadline passes. The robust deadline is an experimental oracle choice, not a hardware timing guarantee; it exceeds the slowest HSI timer period (about 10.101 ms) and leaves room for interrupt handling in this fixture. Phase 0 only establishes this fixture's behavior.

## Simulator survey and choice

| Dimension | Renode | QEMU |
| --- | --- | --- |
| CPU time | `PerformanceInMips` changes virtual instruction throughput; the documented default is 100 MIPS ([time framework](https://renode.readthedocs.io/en/latest/advanced/time_framework.html)). This is an emulation parameter, not a calibrated CPU cycle model. | `-icount shift=N` assigns 2^N virtual ns per instruction; QEMU explicitly says this is not cycle accurate ([QEMU options](https://www.qemu.org/docs/master/system/qemu-manpage.html)). |
| Timer frequency | Platform descriptions expose peripheral and SysTick frequency fields; the STM32F4 NVIC field is used here ([platform source](https://github.com/renode/renode/blob/master/platforms/cpus/stm32f4.repl)). | Virtual clock derives from instruction count in icount mode; changing the shift changes virtual time per instruction ([QEMU icount](https://www.qemu.org/docs/master/devel/tcg-icount.html)). Board-specific timer clock changes require further investigation. |
| Interrupt control | CPU hooks can run at interrupt begin/end, and bus hooks can observe peripheral access ([Python hooks](https://renode.readthedocs.io/en/latest/basic/using-python.html)). | Record/replay logs asynchronous inputs and synchronizes interrupt events, but a general bounded interrupt-delay injection hook is not established by these docs ([record/replay](https://www.qemu.org/docs/master/system/replay.html), [developer replay](https://www.qemu.org/docs/master/devel/replay.html)). |
| Peripheral delay | Local time-source scheduling supports model events at chosen virtual times ([machine connections](https://renode.readthedocs.io/en/latest/networking/machine-to-machine-connections.html)). | Device-model timers use virtual time in icount mode; custom delay injection would need device/model work ([developer replay](https://www.qemu.org/docs/master/devel/replay.html)). |
| Quantum | Synchronization quantum controls the maximum skew between time sinks; it is configurable ([time framework](https://renode.readthedocs.io/en/latest/advanced/time_framework.html)). We use 1 µs as a numerical resolution setting, not as a legal hardware perturbation. | Icount gives instruction-based virtual time and replay; quantum-style machine synchronization is not the chosen mechanism ([QEMU icount](https://www.qemu.org/docs/master/devel/tcg-icount.html)). |
| Replay | Seed, full platform config, hashes, sampled event trace, and simulator version reproduce the deterministic single-machine experiment. | QEMU has built-in `rr=record/replay` event logs when using icount ([record/replay](https://www.qemu.org/docs/master/system/replay.html)). |

**Recommendation:** Renode for the first simulator arm because it directly exposes the STM32F4 SysTick frequency in a board model. QEMU remains valuable for later cross-simulator checks where the same board/peripherals can be modeled. Zephyr Twister explicitly supports Renode simulation and board `renode` metadata ([Twister documentation](https://docs.zephyrproject.org/latest/develop/twister/index.html)); Phase 1 has now built and run upstream ztest suites through a direct Renode runner. Renode's integer MIPS setting makes this particular HSI perturbation model limited, as detailed below.

**Physical-board recommendation for a later validation arm:** STM32F4 Discovery with STM32F407VG. Renode ships a board/platform description for it, and the firmware exercises its SysTick and PD12 GPIO. A physical copy could later check whether the same binary's event timing falls in the modeled range. No purchase is assumed.

## Future experimental controls

- Freeze every agent suite before timing runs. Record prompt, model name/version, generation date, `k`, all inputs, output hashes, and API/token cost.
- Compare human ztest suites against agent suites on the same firmware functions. Tag fixed sleeps, premature timeouts, ISR/log order assumptions, and unprotected shared-state reads.
- Include nominal reruns, a 5/5 rerun filter, and feasible host-level stress as baselines. Report per-test and per-assumption-type flips with Wilson intervals; define the seed sampling distribution before running.
- Add a context-transfer arm that generates tests with versus without existing ztest files in the prompt. Hold every other prompt field fixed.
- Record assertion count/type before and after repair and require mutation score to stay at least as high. These are future criteria, not Phase 0 findings.

## Approved comparison direction (2026-09-28)

The strongest near-term design is an empirical comparison with a repair evaluation, rather than assuming agents improve existing tests. An optional tool contribution would be **specification-bounded, replay-guided repair**: detect a timing assumption, produce a legal failing schedule and trace, replace the assumption with an observable-event wait that retains a defensible deadline, and reject any candidate that loses assertions or mutation kills. This is a proposal, not an implemented system or an established novelty claim. Compare it with a simple static sleep/timeout scan, a naive longer-wait repair, and a manually written event-wait repair; keep unrepaired and unrepairable cases in the denominator.

For each eligible task, pair the original upstream human ztest and agent-generated suites with the same firmware feature, behavioral specification, stimulus, board model, nominal build configuration, and frozen schedule set. Generate agents from the specification and relevant production code without exposing the human test in the main arm. A separate, explicitly labeled prompt-context arm can show whether agents copy human timing patterns. Score nominal correctness and oracle strength before measuring timing flips; a test that never checks the intended behavior is not a robust success. Pin upstream commit and license, preserve original source and built artifact hashes, and report test and subject inclusion/exclusion decisions before looking at perturbation outcomes. Candidate repairs become new frozen test versions.

**Binary identity nuance:** Upstream ztests are compiled into the target image. Comparing human, generated, and repaired suites will therefore usually require distinct full ELFs, even if production firmware sources are identical. The invariance requirement applies **within each test version across nominal and perturbed schedules**: freeze its full ELF and test code and record both hashes before schedule execution. If we claim one identical production firmware binary across test versions, use a separately loaded firmware image and an external test controller; do not make that claim for linked ztests.

**Open-source candidate leads and selected subject:** Zephyr's [GPIO callback test](https://github.com/zephyrproject-rtos/zephyr/blob/main/tests/drivers/gpio/gpio_basic_api/src/test_callback_trigger.c) triggers an interrupt through GPIO and uses `k_sleep(K_MSEC(1000))` before asserting callback counts; it remains an unbuilt candidate. Zephyr's [kernel timer API tests](https://github.com/zephyrproject-rtos/zephyr/blob/main/tests/kernel/timer/timer_api/src/main.c) include fixed busy waits and event synchronization (`k_timer_status_sync`); this application is now built and passing nominally in Renode as one Phase 1 subject. These are real upstream test patterns, but the waits may be justified. Zephyr's [ztest documentation](https://docs.zephyrproject.org/latest/develop/test/ztest.html) and [Twister Renode configuration](https://docs.zephyrproject.org/latest/develop/twister/index.html) support the route in principle; we use a direct Renode runner because this board's Twister Renode runner was not established. The [STM32F4 Discovery board](https://docs.zephyrproject.org/latest/boards/st/stm32f4_disco/doc/index.html) has relevant GPIO and SysTick hardware. The [STM32H7 Renode Reference Platform](https://docs.zephyrproject.org/latest/boards/antmicro/stm32h7_renode_reference_board/doc/index.html) explicitly documents both physical and Renode runners, making it another candidate; no subject switch has been made.

An existing fixed wait is a **candidate assumption**, not a defect. Perturbation must cross a failure boundary inside a documented legal hardware range, and classification must still separate test brittleness, firmware behavior, simulator error, and unknown. Do not tune perturbation bounds around a chosen test's sleep constant. If legal bounds do not flip many upstream tests, report that negative result and assess feasibility before expanding the corpus.

### Phase 1 implementation and registered pilot

The selected first corpus is ten nominally passing **upstream Zephyr ztest applications** from pinned v4.3.0, all built for STM32F4 Discovery with a study-owned HSI clock overlay. These are independent firmware test ELFs, but one upstream repository and one board; this is narrower than ten independent codebases. An eleventh STM32 EXTI suite built but failed all three cases at nominal timing in Renode and is excluded from flip-rate denominators with its raw output retained. The precise seed set, eligibility rule, oscillator bound, simulator approximation, and analysis units were registered in [`subjects/phase1_zephyr/PROTOCOL.md`](../subjects/phase1_zephyr/PROTOCOL.md) before running the perturbed baseline. The 30-seed rate is a Phase 1 pilot baseline; Phase 3 should expand to 100 or more seeds on the frozen suite set. Because Renode cannot express fractional MIPS at this setting, the oscillator inputs are hardware bounded but the simulated CPU-to-SysTick coupling remains model limited.

**Observed Phase 1 outcome:** 299/300 prespecified eligible runs passed; one `sleep` run had a startup harness error before virtual time advanced. There were no observed eligible flips, and all 20 exact endpoint challenges passed. This is a negative result for the selected perturbation and a baseline for comparing future agent suites, not an efficacy result for agents. See [`notes/PHASE1_REPORT.md`](../notes/PHASE1_REPORT.md) for denominators, per-subject Wilson intervals, replay results, and exclusions.

### Approved Phase 1 extension: independently clocked RTC alarm

The user approved one additional timing dimension before Phase 2. The [registered protocol](../subjects/phase1_lsi_rtc/PROTOCOL.md) selects upstream Zephyr v4.3.0 `rtc_api.test_alarm_callback` on STM32F4 Discovery. A study wrapper links the exact upstream C files and enables the supported second/minute/hour alarm mask. This is a **selected configuration of one upstream test**, not an eleventh independent project or an unbiased prevalence sample. The full upstream RTC suite is retained as a separate nominal compatibility pilot. Neither result is pooled with the ten-subject HSI baseline.

The board's RTC uses the independent LSI oscillator. [ST's STM32F407 datasheet, Table 35](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) specifies 17–47 kHz (typical 32 kHz) at VDD 3 V over −40 to 105 °C. The [Zephyr STM32 RTC driver](../subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c) sets 128 × 250 prescalers for nominal 32 kHz LSI. [Renode's STM32F4 RTC model](https://github.com/renode/renode-infrastructure/blob/master/src/Emulator/Peripherals/Peripherals/Timers/STM32F4_RTC.cs) exposes the RTC input frequency separately from CPU/SysTick. The experiment varies only that model input within the datasheet range, with the same full ELF and test source across one nominal, 30 registered seeded, and two endpoint runs. The sampled frequency distribution and environmental limitations are in the protocol.

The test expects an alarm ten RTC seconds after setting time, then asserts the callback after a fixed 3 + 10 seconds of Zephyr sleep. That deadline implicitly assumes the LSI tick rate is sufficiently close to nominal. An observed failure still requires exact replay and the four-way decision procedure below. A later event-wait repair must retain the no-premature-callback assertion and a defensible upper bound; merely extending the sleep is a comparison control, not a validated repair.

**Observed extension result:** the selected upstream case passed at nominal 32 kHz, flipped on 7/30 prespecified seeded LSI frequencies (23.3%; 95% Wilson interval 11.8–40.9%), failed at the 17 kHz endpoint, and passed at 47 kHz. Every failure replayed identically. Register and callback-flag probes at 17 kHz and the highest failing seed show late callback arrival; the eight failures are classified as model-specific brittle test assumptions under the written four-way rule. See [`notes/PHASE1_LSI_REPORT.md`](../notes/PHASE1_LSI_REPORT.md). This is a selected configuration of one upstream case and does not establish a prevalence rate or agent improvement. The user reviewed this extension and authorized Phase 2; no repair has begun.

**Review gate before agent generation.** The user approved option 2 from the initial Phase 1 review: add an independently clocked peripheral with a documented hardware range. The RTC extension above implements that option; its result remains separate from the HSI baseline. Do not widen the HSI range or tune any bound around a test constant merely to create flips. Obtain the user's review of the RTC extension before generating agent tests.

### Phase 2 frozen generation and validity gates

The user approved the Phase 2 comparison after reviewing the RTC extension. The [Phase 2 protocol](../generated/phase2/PROTOCOL.md) and [11-task manifest](../subjects/phase2_tasks.json) define five independent generations per task. Ten tasks map to passing HSI upstream cases; the RTC callback task remains a separate selected LSI stratum. The prompt gives a behavior specification, required checks, public API hints, and build configuration. It does not expose matched upstream test source or prior timing outcomes. The shared prompt template, task manifest, response schema, and requested model are hash-locked in the primary generation manifest.

The first Sol sample is retained as a feasibility pilot. The primary 55-run cohort uses `gpt-6-luna`, recorded before its first generation, because the account's five-hour Sol usage was nearly exhausted. The authenticated CLI returns the requested model slug and its CLI version, but its event log does not identify a dated server model snapshot; that exact version is unavailable and must be reported as such. Sampling seed and temperature are also unavailable for this route. Each process is independent and its exact prompt, raw CLI events, response, source hash, date, and token usage are archived. The cost log reports billed dollar cost as unavailable, rather than zero.

Before Phase 3, build each frozen C source without editing it, save the full ELF hash, and run one nominal Renode execution. Preserve compile failures, nominal failures, and oracle-inadequate suites in the generation denominator. Judge oracle adequacy against the registered `required_oracles` before seeing perturbed outcomes. Static tags identify candidates for fixed waits, timeouts, ordering, and shared-state reads in both matched upstream tests and generated suites; a tag alone is not proof of an unjustified assumption. No legal schedule variation or repair is part of Phase 2.

All 55 primary Luna outputs were generated in one independent CLI attempt each; the raw event streams show no tool use. The generation calls completed despite the app usage display reaching its five-hour limit during the batch. Of 55 outputs, 50 compiled, 38 passed nominally, and 34 met every registered oracle in the **original strict** source review; two oracle judgments remain uncertain. Compile failures, nominal failures, timeouts, and oracle-inadequate suites remain in the denominator. The RTC prompt did not state the registered 17–47 kHz LSI range even though it required a justified finite callback deadline. The sole nominally passing RTC output imposes 15 s, below the approximately 18.8 s needed at legal 17 kHz; no primary RTC agent output passed both nominal and the **original strict** oracle gate. The later dated split-gate amendment above retains that source as functionally adequate and timing inadequate. See [Phase 2 report](../notes/PHASE2_REPORT.md).

### Separately registered RTC context supplement

After reviewing Phase 2, the user approved [a five-sample supplement](../generated/phase2_rtc_bound/PROTOCOL.md). Its only task-content change was `rtc_alarm_callback.api_hints`: the public RTC signatures, ST's 17–47 kHz LSI range, the driver's 128 × 250 divider, the 18.824 s slow-end calendar calculation, and the distinction between that calculation and unbounded ISR-to-thread delay. The same three required oracles, feature specification, board, build, template, schema, and requested Luna model were retained. This is one separate context condition for the selected RTC task, not an independent subject or an extension of the original 55 denominator. It remains distinct from the future proposed context arm that would expose human test source.

All five supplemental outputs were frozen. Three failed compilation, one compiled but failed its nominal pre-alarm predicate, and one passed nominally but required its second callback with `K_NO_WAIT` after the first. Without a documented zero-separation guarantee, that last suite fails the original justified-bound oracle. Thus **0/5** supplemental suites pass both nominal and the **original strict** oracle gate, despite using 24–30 s main deadlines that cover the documented slow-clock calendar arrival. The later split gate counts the sole nominal pass as functionally adequate and timing inadequate, separately from the primary cohort. At the Phase 2 stop, no supplemental agent schedule had been varied, so there was no RTC agent flip rate or improvement claim. The 34 eligible primary HSI suites remain candidates for Phase 3; a further RTC generation condition would need a fresh registered design decision. See [supplement report](../notes/PHASE2_RTC_SUPPLEMENT_REPORT.md).

### Phase 3 RTC arm and HSI decision gate

The [RTC Phase 3 protocol](../subjects/phase3_rtc/PROTOCOL.md) registers 100 legal LSI frequencies for the unchanged selected upstream test, the nominally passing primary Luna RTC test, and the nominally passing RTC-context supplement test. Both agent suites were oracle-inadequate under the **original strict** gate. The later split gate makes Luna `r04` a primary functionally adequate timing-brittleness case and keeps the supplement separate; neither is a robust-test success merely because it passes a schedule. The 100-seed list, source/ELF hashes, Renode version, and trace settings remain locked in the [plan](../subjects/phase3_rtc/plan.json). Five nominal repeats precede seeds. This arm does not mix the primary and supplement generation denominators.

The HSI choice was resolved by the user's 2026-09-29 instruction to use the 100-MIPS approximation. In the earlier direct [Renode 1.17.0 probe](../results/phase3_hsi_probe/fractional_mips_probe.json), setting `PerformanceInMips` to 15.84 read back as 15, so the old 16-MIPS setting could not track ±1% CPU drift. The new registered plan permits 99–101 integer MIPS and requires fresh nominal screening, but still rounds intermediate frequencies. Neither model automatically establishes a silicon-legal full execution schedule; the documented HSI input range and emulator CPU abstraction are reported separately.

## 2026-10-01 RTC threshold audit and proposed context factor

The completed selected RTC callback report now compares each test's source wait with the `320,000/f_LSI` calendar calculation and the saved 100-seed verdicts. This is an analysis of already frozen inputs, not a new schedule or a gate change. It finds no evaluable seed disagreement with the 13 s, 15 s, and 26 s calendar windows; the supplement's 26 s consists of a 2 s pre-alarm sleep followed by its 24 s callback timeout. Its immediate second-callback `K_NO_WAIT` remains a timing-bound inadequacy that LSI-rate variation does not challenge.

The user authorized the already registered 100-MIPS HSI arm after RTC completion. Its first launch was a sandbox/monitor-history infrastructure error before virtual time advanced and is preserved outside a fresh five-run qualification screen. The HSI runner uses the existing locked plan and writes hashes, settings, raw logs, and traces for every run.

**2026-10-02 completion.** The [final HSI report](../notes/PHASE3_HSI_100MIPS_REPORT.md) audits 4,606 qualified runs from 44 candidates. Fresh nominal screening admitted ten upstream selected cases and 33 of 34 Luna HSI suites; the other Luna suite had one nominal startup harness error and was not varied. The eligible versions produced 0/943 upstream and 0/3,270 Luna seeded assertion failures on evaluable runs. Eighty-seven seeded and one nominal records ended in harness errors at virtual time zero; all 88 passed separate fresh-process diagnostics, but their original verdicts remain non-evaluable. Every exact endpoint challenge passed. The absence of HSI flips is a negative result for this bounded, quantized Renode arm, not full timing adequacy or a model advantage. No Sol/Astra generation was started.

The `spec in context` factor was drafted on 2026-10-01 and approved on 2026-10-03. Its implementation and preregistered comparisons appear at the top of this document; the earlier bound-context RTC supplement is not a balanced factor cell. The 2026-09-29 v2 cross-model lock remains an immutable historical design record and is superseded for new generation by the versioned 390-call factorial.

## Flip decision procedure

Assign **exactly one** label per flip. Preserve unknowns in the denominator and a separate table.

1. Confirm firmware/test hashes, simulator version, schedule bounds, seed, and trace. Replay the failing seed. If replay diverges or inputs are missing, label **unknown** pending investigation.
2. Check whether the observed firmware behavior violates its written functional/timing specification. If yes, and the model/input is credible, label **genuine firmware race/bug**. Use the interrupt-concurrency taxonomy after verifying its source.
3. If the observed behavior depends on an invalid or inaccurate simulator/peripheral behavior, label **simulator/peripheral-model artifact**. Seek cross-simulator or physical confirmation for a sample.
4. If the firmware behavior is allowed by its specification, the test's asserted condition becomes true within the valid window, and only the test's timing assumption causes the failure, label **brittle test assumption**.
5. If evidence cannot distinguish these, label **unknown**. Do not silently discard or reassign it.

Hardware validation later uses a Raspberry Pi Zero to drive and measure seeded GPIO stimulus only after measuring achieved jitter. MSPM0 and ESP32 remain candidates requiring model/capability verification.
# 2026-10-06 UTC amendment: RTC quality faults and exploratory delivery latency

The original 1 Hz nonarrival clock mutant crashed Renode before a reference verdict, so it is invalid and is never scored. The 10 kHz late and 64 kHz early operators activated on all three task-specific reference tests. Score these two operators now as an explicitly interim two-fault mutation result for all 66 eligible AI suites and three upstream selected cases at nominal host/CPU settings. Preserve the original failed activation record and use a new manifest/result namespace. Register a replacement nonarrival operator outside the RTC clock path, validate activation on all three reference tests before scoring it, and retain the two-fault score if no replacement validates. A **strict kill** requires an explicit failing selected ztest case; pass is survival, and simulator timeout/unknown/harness error is reported separately without being coded as a kill. Report both numerator and evaluable/planned denominator per suite and cohort. Fault injection is a test-quality challenge, not a legal hardware schedule or an RQ2 seed.

The separate exploratory delivery-latency pilot uses nominal 32 kHz LSI and targets all 21 measured AI RTC suites coded with definite latency/ordering assumptions, a fixed-seed random sample of the 23 measured zero-clock-failure suites coded unknown, and the three matched upstream tests. Freeze the sampled IDs, driver/ELF hashes, delay levels, and achieved-delay evidence before interpreting outcomes. Proposed levels are 1 ms, 10 ms, and one RTC calendar tick (1,000 ms); these magnitudes are **plausible, not datasheet-legal**. Include a zero-delay control for each rebuilt variant. The pilot is exploratory and excluded from clock-induced flip rates. First validate that an isolated RTC driver variant delays the intended observation/delivery path without changing nominal RTC frequency or causing startup failure. If implementation and execution exceeds a few hours, stop and seek review under the user's 2026-10-06 instruction.

The final report must show all 37 observed AI clock failures in three range-absent suites, zero in range-present suites, with measured and hybrid denominators separate. Mutant scores, source-coded latency categories, wait styles, padding, nominal runtimes, and static upstream threshold findings are descriptive test-quality outcomes. Keep task clustering and missing verdicts explicit.

## 2026-10-07 approved alarm-calendar-offset quality arm

The user approved a separate firmware-level alarm fault at nominal 32-kHz LSI. The isolated STM32 RTC driver copies each requested alarm time, programs a value one RTC calendar second early or late, and leaves the calendar clock and test sources unchanged. The signed compare value, driver/source hashes, selected case, ELF, nominal platform, simulator version, UART, and trace are registered in [the v1 manifest](../results/rtc_alarm_offset_v1/manifest.json). This is an intentionally faulty rebuilt ELF, never a legal-clock RQ1 verdict. The scored alarm denominator is 39 eligible LLM-generated callback/pending suites plus the two upstream (human) alarm tests. Twenty-seven LLM-generated counting suites and the upstream (human) counting test run as non-activation controls, outside alarm kill rates. Each variant must make both task-specific alarm references fail a programmed-alarm readback assertion; nominal controls and both counting references must pass. Count a kill only with a logged active signed offset and an explicit selected-case failure. Pass means survival, absent activation is unscored, and harness errors remain missing. Replay explicit kills separately without replacing originals. The [dated operator proposal and preregistration](../notes/RTC_FIRMWARE_ALARM_OFFSET_PROPOSAL.md) records the rationale and earlier runtime estimate.

**2026-10-08 completion.** The [alarm-offset report](../notes/RTC_ALARM_OFFSET_V1_REPORT.md) audits all 138 originals: 73 activated explicit kills, six survivors, three missing alarm verdicts, and 56/56 counting non-activation passes. All 73 kills replayed with matching selected-case verdict, error field, and signed programming log. LLM-generated alarm suites killed the early offset in 38/38 evaluable runs and the late offset in 34/38; the upstream (human) callback survived both, while upstream (human) pending killed late and had a missing original early. Diagnostic reruns of the three missing cases are retained separately and do not enter scores. The paper presents this as a nominal-clock firmware-fault quality probe, separate from legal-clock RQ1 and out-of-spec oscillator challenges. No repair or dynamic delivery-latency arm was started.

## 2026-10-08 assertion-level alarm-offset interpretation

The [offset assertion ledger](../analysis/rtc_alarm_offset_v1_assertion_audit.csv) records each scored kill's first failing UART assertion and frozen source line. Of 73 explicit kills, 41 first fail alarm-register readback, 18 first fail a callback-before-RTC-target guard, 13 first fail an exact callback or observation calendar check, and one Sol late callback fails a composite ID/read/calendar flag whose immediate cause is unresolved. This supports separate claims about programmed-compare correctness and event timing; the aggregate 73-kill count must not be described as 73 direct firing-time checks. The four late-offset survivors are all Sol callback suites with no exact upper target-second assertion; their scalar clock-only padding class is unknown. A newly labeled upstream (human) pending early diagnostic failed readback, but its original remains missing. The manuscript comparison is bounded to the selected upstream cases, only two of which exercise alarms.
## 2026-10-08 manuscript interpretation clarification

The frozen callback generation specification required both callbacks at the configured RTC time; the pending specification required alarm readback. These instructions were unchanged by the range-present factor. The nominal-clock offset probe therefore supports a task-matched description of generated callback oracle precision, not a causal claim that model authorship alone produced that precision. Report upstream callback (0/1 per sign) beside eligible generated callback cases (18/18 early, 14/18 late among evaluable originals); report pending separately because its kills chiefly reflect programmed-alarm readback. Keep original missing verdicts unscored and preserve the suite/task clustering and selected two-case upstream alarm baseline.
## 2026-10-08 Stage A fairness re-analysis amendment (before new Stage A computations)

The user requested a read-only re-analysis of the already frozen factorial and RTC artifacts. No frozen source, ELF, schedule, raw record, or generated response will be edited or rerun. The existing all-attempt aggregate and RTC outcomes were already visible before this amendment; this is a transparent post-result analysis, not a prospective hypothesis test. Stage B remains proposals only and Stage C requires separate approval.

**A1 all attempts.** Use each of the five saved generations in every model × prompt × task cell. Partition attempts in this order: build failure; built but functional-gate failure; built/functionally adequate but failure of the five-launch nominal gate; eligible. For RTC tasks, mark legal-clock outcomes as measured complete pass, observed assertion flip, measured zero-flip with missing verdict, or unrun frozen prediction. Report confirmed working clock-robust yield only for eligible suites with all 100 original seed verdicts passing; report a separate possible upper yield that includes zero-failure predictions and incomplete zero-flip suites. The combined quality outcome additionally requires a source-coded scalar clock budget at most twice the legal slow-bound arrival (not over-padded), an explicit late-fault kill, and an explicit nonarrival-fault kill. Unknown padding, missing fault verdicts, and unrun clock vectors cannot be counted as confirmed successes. Report by model × prompt × RTC task, with all five attempts retained in denominators. HSI factorial varied runs remain deferred.

**A2 tests.** Fisher's exact test is two-sided over suite-level any-flip yes/no in measured RTC suites, separately per task and descriptive pooled cells; show cells too sparse for meaningful inference. McNemar's exact test uses discordant pass/fail pairs on identical registered seed frequencies for each measured eligible AI suite against its matched upstream selected case; report missing pairs separately and aggregate only with task/suite clustering explicitly flagged. The independent unit is not a seed for population inference. Wilson intervals remain descriptive. No significance claim is made for predictions or missing verdicts.

**A3 similarity.** Compare each of the 66 eligible RTC generated suites to the selected upstream test of the same task using only frozen source and existing probe records. Fault-profile agreement uses five operator outcomes (fast, slow, nonarrival, early and late alarm offsets); non-activating counting offsets and any missing verdict are excluded from the pairwise denominator, never treated as agreement. Oracle categories are eventual occurrence, not-before, exact calendar time, upper bound, register readback, and count/ID; a single assertion may carry multiple categories. Maintain an auditable per-assertion source ledger and report category distributions with unknown/ambiguous tags. API similarity is Jaccard overlap of statically extracted Zephyr function calls after excluding ztest assertions and C control/macro words; report both call sets. Surface similarity is a reproducible normalized token-sequence similarity after stripping comments/whitespace, used as a copying flag, not proof of training exposure.

**A4 and A5.** Derive ideal RTC arrival $t=320000/f$ for the saved 100 frequencies and compare only with observed timestamp fields that actually record alarm/calendar arrival; do not infer time from a pass/fail threshold alone. Report coverage, error, and the reference-oracle results; classify the evidence as Renode internal consistency rather than physical fidelity. For the three selected and 33 statically scanned upstream files, code observable patterns (eventual occurrence, window/deadline, polling, readback, delivery-latency check) from source with unknown retained where hardware/API contracts are absent. These source classifications are descriptive, not executed outcomes for the other 30 files.

**2026-10-08 A3 scope clarification before the remaining source metrics.** The source similarity inventory will include all 90 RTC generations (five per model, prompt, and RTC task), including gate failures. Five-fault profiles remain available only for the 66 eligible suites actually probed; unavailable, non-activating, and missing operators receive no similarity score. The first eligible-only source ledger is retained as an intermediate analysis artifact and is superseded by the all-attempt source inventory.

**2026-10-08 A1 reporting-scope clarification.** The paper's compact all-attempt table will show the three RTC tasks, where legal-clock and fault probes exist. A separate machine-readable 78-cell ledger will report gate outcomes for every model × prompt × task across all 13 tasks and mark the ten factorial HSI tasks' clock/fault outcomes as not run. No inference of HSI robustness or fault detection will be made from nominal passes.

## 2026-10-08 model-differences re-analysis and Stage B proposal amendment

Before computing the additional model comparisons, retain all 15 saved RTC attempts per requested model ID and prompt condition. A **working** attempt passed build, functional source gate, and five nominal runs. A **confirmed clock-robust** attempt is working and has 100 original legal-LSI seeded passes with no missing verdict. A **confirmed robust plus slow/nonarrival-killing** attempt additionally has explicit selected-case kills under the 10-kHz slow-oscillator and driver-path nonarrival probes. The latter measure does not require the separate source-coded padding threshold; report that distinction. Forecast-only and incomplete original clock vectors never count as confirmed successes, and missing nonarrival originals are unscored. Summarize each count over all 15 attempts, per model and prompt.

Use two-sided Fisher exact tests for pairwise between-model comparisons of working yield, confirmed robust yield, and the robust-plus-two-kill yield separately within each prompt condition. Also compare any observed clock flip among measured eligible suites, where cells permit. Treat these as post-result descriptive tests with no multiplicity-adjusted claim, report all non-significant contrasts, and retain task clustering, unequal task eligibility, missing verdicts, and missing backend model version snapshots as limitations. The model IDs refer to calls saved on October 3--4, 2026 UTC, not known immutable model snapshots.

Stage B is **proposal and packet preparation only**. Develop one combined RTC generation-round proposal with a looser upstream-style specification and a reminder-only condition for callback, pending, and counting across all three requested models. Specify exact proposed prompt insertions/replacements, sample size, gates, clock and fault evaluation, kill criteria, runtime, and token/cost assumptions before any generation. Prepare a same-spec human author packet without recruitment or submissions. B3, B5, and B6 receive feasibility notes only. No Stage B simulation, model generation, human recruitment, or change to an existing lock is authorized by this amendment.

## 2026-10-08 approved Stage B callback exploratory round (recorded 18:29 UTC before generation)

The user approved the Stage B generation round with five independent suites per model and condition, prioritizing callbacks within the earlier runtime estimate. This amendment supersedes the proposal's two-per-cell, three-task pilot. The four conditions are `loose_spec`, `reminder_only`, a fresh `range_absent` control, and a fresh numeric `range_present` control. The three requested model IDs are `gpt-6-luna`, `gpt-6-sol`, and `gpt-6-astra`. The sole task in this round is `rtc_alarm_callback`: **5 × 3 × 4 = 60 intended calls**. A complete pending block would add 60 calls and exceed the prior 72-call estimate, so pending and counting are deferred, not silently pooled or partially sampled. All results are exploratory; historical factorial results remain a separate cohort. B3, B5, B6, and human recruitment remain deferred.

Before the first call, freeze the exact prompt bytes for all four conditions, response schema, generation runner, five-replicate interleaved call order with seed 20261008, model IDs, available CLI version, build/nominal configuration, 100-seed legal LSI map, endpoint settings, selection rule, fault operators, and output paths under `generated/stage_b_callback_v1` and `results/stage_b_callback_v1`. Each call is source-only, without tool or local-file access; preserve raw events, failed attempts, metadata, source, and hashes. No generated source may be repaired. A CLI infrastructure failure may be retried under identical inputs with the failed attempt retained. Do not alter historical prompts, sources, ELFs, locks, or raw results.

For **all 60 intended attempts**, report generation/schema, build, functional source review, timing-bound adequacy, and five fresh nominal verdicts separately. An eligible suite builds, meets its condition's functional contract, and passes all five nominal runs. In the looser condition, exact target-second and alarm readback checks are optional quality outcomes, never functional-gate requirements. In the other three conditions, use the original callback specification and amended functional gate. Source review precedes varied-clock and fault outcomes; retain uncertain judgments as unknown.

Every eligible suite receives 17- and 47-kHz legal LSI endpoints. Before any 100-seed runs, record a clock-only per-seed forecast if a source provides a defensible scalar threshold; otherwise mark not predictable with its reason. Select at most one eligible suite per model × condition (12 total) for the frozen 100-seed schedule, by lowest SHA-256 rank of `20261008|suite_id` among eligible suites in that cell, regardless of predictability. This outcome-blind selection can be made after gates but before clock or fault results. Demand exact per-seed agreement for sampled predictable suites. On any mismatch, stop further varied-clock runs, retain the discrepant original and replay trace, and return for review. Unrun predictable suites remain forecasts; unrun nonpredictable suites remain unknown, even if endpoints pass. Missing verdicts are not passes. Report all-attempt and measured-sample denominators separately; do not infer a field failure probability.

At nominal 32-kHz LSI, challenge every eligible suite with the already validated 10-kHz slow oscillator, driver-path nonarrival, and signed −1/+1 RTC-calendar-second alarm offsets. The 64-kHz fast oscillator is an optional separately labeled quality probe only if it fits the same batch; it is not needed for the approved minimum. Reuse operator semantics but build new isolated ELFs and write to the new result namespace. Confirm reference activation against the same reference sources before scoring. Count a kill only with logged operator activation and explicit failing selected ztest case; pass is survival; startup/monitor/ambiguous errors remain missing. Offset comparisons are callback versus callback. Replay and classify observed legal-clock failures separately; diagnostics never replace original verdicts. Analysis is task-matched, with five suites clustered within the one callback task. Any Fisher or other statistical contrast is exploratory, with missing/predicted outcomes separated.

The prior estimate for a 72-call pilot was 8–15 wall hours plus 3–6 hours of adapter work, and roughly $7.60 API-equivalent at historical token medians (not an actual CLI billing quote). This 60-call callback round reduces generation volume but may still take longer if build or simulator records are slower; record achieved wall time and stop if infrastructure or estimate assumptions fail materially. The full approved protocol and lock are in `generated/stage_b_callback_v1/PROTOCOL.md` and `lock.json` once frozen, before any call.

**2026-10-08 infrastructure continuation note (after first generation/build, before any nominal verdict).** The initial sandboxed Codex CLI attempt and one later connection timeout are preserved as failed call attempts; identical-input retries may finalize their intended call. The previously used temporary Zephyr SDK 0.17.4 directory lacked CMake configuration and then `picolibc.specs`; two failed build attempts are retained before an official same-version archive restored the toolchain and a third build passed. The first five nominal launches for one source stopped at virtual time zero because Renode could not write its user-level history file through the sandbox. Preserve all five original harness-error records. A separately named five-launch **access-retry qualification** may be run with the same ELF, platform, parser, schedule, and Renode version through an execution context with user-level history access. It is not a diagnostic substitution for an original verdict: show original and retry columns, and require five retry passes before any varied-clock/fault challenge. If access retries are not possible, the suite remains nominally unqualified. Apply this rule uniformly to other suites whose first nominal attempt has the identical zero-time permission error; never retry a source assertion failure or timeout as infrastructure.

## 2026-10-12 Stage B interruption audit and pause

This dated audit uses only already saved Stage B records; it introduces no new experimental verdict. The locked 60-call order has two finalized sources, both Astra callback r01 (range-present and loose-spec). The range-absent Astra r01 call has two preserved CLI timeouts and no source; no later call has started. Among the five CLI attempts, one range-present attempt failed in the sandbox, three timed out (one loose-spec and two range-absent), and two succeeded. Both finalized sources eventually built. Two failed range-present build attempts were SDK infrastructure failures before the same source built with the restored SDK. The range-present original five nominal launches all failed at virtual time zero from Renode history-file access; five separately labeled access-retry launches passed and meet the registered retry qualification. The loose-spec source had four original nominal passes and one Renode startup timeout, so it fails the frozen 5/5 gate. These infrastructure outcomes are tabulated by condition in [the interruption audit](../notes/STAGE_B_CALLBACK_INTERRUPTION_2026-10-12.md). None is a test assertion failure, and none enters a condition comparison as such.

The user requested a revised estimate before continuing and instructed a stop if the remaining full round exceeds 12 hours. With 58 calls still unfinalized, repeated CLI timeouts, nominal gates, legal-clock challenges, and fault probes remaining, the revised full-round estimate is 14--22 additional wall hours under a working service, with further delay possible if timeouts recur. The generator and idle build watcher are stopped. No Stage B legal-clock or fault run has started. Preserve the 60-call lock and all completed records. A reduced scope requires a new dated amendment and user approval before any new model call or simulation.

## 2026-10-22 Lonestar6 environment and calibration amendment (before new runs)

The user authorized Phase 1 setup and calibration on Lonestar6, allocation
`TRA25006`. The user logs in using MFA and runs the supplied commands;
no credentials are shared with the automated agent. Put the clone, image,
transfer bundle, runtime temporary directories and results under `$WORK`,
never `$HOME` or `$SCRATCH`. Pack records into single-node jobs, not Slurm
arrays. Use the development queue for the resource probe and calibration.
No production run, forecast-only measurement, fault control, repair,
generation, or manuscript update starts before the calibration report and
the user's approval at that checkpoint.

Reuse exact saved ELFs, sources, platform bytes, clock settings and the
original observation/verdict code. The flipping subjects are Sol base
pending r01/r03 and Astra base pending r05. Choose five complete-passing
subjects as the lexicographically first saved suite in each of these
strata: Astra/base/callback, Sol/ranges/callback, Luna/base/counting,
Luna/ranges/counting and Astra/ranges/pending. Every selected suite receives
its 100 saved frequencies and both endpoints, for 816 calibration records.
Selection uses existing results only. Lock original record and trace
hashes, source, ELF and platform hashes, frozen runner dependencies and the
new adapter before submission. Compare verdicts and entire trace-file
hashes exactly; do not normalize differing traces. Execution record hashes
will differ because node, job, container and timestamps are recorded.

First perform one separate resource-probe run of the selected Astra base
callback at 17 kHz, with the same ELF and strict comparison. Measure peak
resident memory and wall time using GNU time on a compute node. Set packed
concurrency to the minimum of the requested cap, allocated CPU count, and
80% of available node memory divided by 1.5 times measured single-run peak
memory. The 1.5 factor is a prospective safety allowance, not a measured
memory bound. Keep per-run resource usage during calibration. A mismatch,
missing verdict, invalid input, or incomplete task blocks further launches.
Already-running packed tasks may finish and remain recorded. Never
replace an original harness error with a retry that passed.

Pin Renode 1.17.0, .NET 8.0.21, Zephyr commit
`3568e1b6d5cdd51a6b964a2a1d6d29200fea2056` and SDK 0.17.4 in the
Apptainer definition. Checksum-pin the Linux downloads and base image.
Seal the built SIF SHA-256 and software inventory before the probe. Every
record stores node, container hash, Slurm job ID, task index and plan hash.
Capture the actual Renode version and stop if it differs from the saved
version. Transfer only the existing SVD cache, not user history or other
configuration, to avoid network downloads on compute nodes. The image and
packed runner remain unvalidated until the user's Linux build, resource
probe and calibration complete. STOP for approval after calibration.
Later experiments require separate dated amendments; the optional LLM
repair arm is not started by this registration.

**2026-10-22 access-boundary addendum, before remote execution:** the user
made an existing `ssh ls6` session available. Use noninteractive SSH;
if it disconnects or requires authentication, stop without attempting to
authenticate. All remote work, including caches and temporary files, is
restricted to `$WORK/zephyr-rtc-clock-robustness`; use its
`tacc_work/20261022` subdirectory for this phase. Do not touch SSH or
account settings. Pull code using `git pull` only, transfer data/results
using rsync, and never push from Lonestar6. Submit builds, probes,
calibration and substantive analyses only to compute nodes. Development
jobs are authorized under `TRA25006`; every normal-queue submission
requires a separate job/node/time/SU report and explicit approval.

**2026-10-22 module-pinning addendum, before image build and calibration:**
Load `tacc-apptainer/1.4.1` and `launcher/3.10` explicitly. Pack one
`apptainer exec` invocation per jobfile line with TACC Launcher, using the
resource-probe-derived process count. Record the actual Apptainer version
as well as the SIF SHA-256 in every run. Do not use the default Apptainer
1.1.8 module or GNU parallel for this calibration.

**2026-10-22 infrastructure correction, before image build or Renode data:**
Development build job 3529750 stopped during module loading because the
Apptainer shell-completion script referenced an unset optional variable
under Bash nounset. Temporarily disable nounset only while loading the two
pinned modules, then restore it; retain errexit and version checks. Preserve
the failed job logs. Seal a new v2 transfer bundle with updated code hashes
and use a separate `tacc_work/20261022-v2` base for the next build. Suite
selection, saved inputs, calibration comparisons and stopping rules do not
change. No image was built and no Renode run occurred in the failed job.

**2026-10-22 package-version string correction, before image build or Renode data:**
Development job 3529760 loaded the correct pinned module, whose executable
reports `apptainer version 1.4.1-1.el8`. Accept this exact TACC RPM package
string in addition to upstream `apptainer version 1.4.1`; continue recording
the full string and requiring the pinned module. No other runtime version
is allowed. The job stopped before image creation. Preserve its logs and
seal v3 code/input hashes for a new `tacc_work/20261022-v3` build directory.
The selected tests, inputs and all calibration criteria remain unchanged.

**2026-10-22 WORK-only fakeroot helper, before image build or Renode data:**
Development build 3529805 verified inputs but failed during apt package-list
setup: LS6 supplied a root-mapped namespace without a fakeroot command or
subuid mapping, so setgroups/seteuid failed. Dependent resource job 3529827
was cancelled without running. Use Apptainer's documented host-helper mode
by compiling fakeroot 1.37.1.1 as the ordinary user on a development node,
solely under `tacc_work/20261022-v4/tools`, before building the image. Its
Debian source URL is
https://deb.debian.org/debian/pool/main/f/fakeroot/fakeroot_1.37.1.1.orig.tar.gz
and SHA-256 is
`86b0b75bf319ca42e525c098675b6ed10a06b76e69ec9ccf20ef5e03883b3a14`,
matching the official source-control `.dsc` checksum obtained over HTTPS.
Record compiler, helper file hashes, node/job and helper-inventory hash in
the image provenance. Do not alter subuid/subgid, account, SSH or system
configuration; do not use sudo. Inspecting Apptainer v1.4.1 source confirmed
that build configuration disables the usual home mount and passes explicit
binds; add a WORK-home marker check before any package commands as a guard.
Seal a separate v4 code/input bundle; preserve all failed-build logs. The
Renode/.NET/Zephyr/SDK pins, test selection, trace comparisons and stopping
rules remain unchanged. No image or Renode result exists from v3.
Reference: https://apptainer.org/docs/user/1.4/fakeroot.html (host-helper mode).

**2026-10-22 helper-header compatibility correction, before image or Renode data:**
Development job 3529840 verified the frozen inputs and helper source hash,
but its configure test found a capset symbol without `sys/capability.h`;
fakeroot compilation then failed on the missing capability typedefs.
Dependent probe 3529851 was cancelled without running. Disable only this
optional fakeroot wrapper with the configure cache `ac_cv_func_capset=no`,
and record that setting in helper provenance. Do not add system headers,
change kernel capabilities or account settings. Preserve v4 logs and use
a separately sealed v5 bundle and `tacc_work/20261022-v5`. Other helper
options, source hash, simulator/toolchain pins, inputs and calibration
criteria remain unchanged. No image or Renode run occurred in v4.

**2026-10-22 build temporary-storage correction, before image sealing or Renode data:**
Build 3529884 successfully compiled the WORK-local helper and passed apt
setup. Further inspection of Apptainer v1.4.1 source showed that its build
configuration disables automatic home mounting but retains automatic
host `/tmp` and `/var/tmp` mounts. APPTAINER_TMPDIR redirects build bundles,
but does not by itself redirect those mounts inside `%post`. The build log
shows pip temporary paths and the Renode download under `/tmp`, so v5 may
have created and cleaned temporary build files on the compute node outside
the authorized WORK tree. This is a storage-boundary deviation, not an
experimental result. Build 3529884 was cancelled after 4:23; dependent probe
3529889 was cancelled without running. Do not inspect, delete or otherwise
modify files outside the authorized project to clean up the prior attempt.
No existing user-data modification was observed, and no simulation ran.
For v6, explicitly bind WORK-backed build-tmp and build-var-tmp directories
to both paths during image build and inventory execution. Check unique
WORK markers before package installation and during `%test`; retain the
WORK-home guard and all existing cache settings. Preserve v5 logs, seal a
new v6 bundle and use `tacc_work/20261022-v6`. All tool pins, selected inputs,
verdict/trace criteria and stage approval gates remain unchanged.
Source inspected: Apptainer v1.4.1, pkg/util/apptainerconf/config.go and
internal/pkg/runtime/engine/apptainer/container_linux.go.

**2026-10-22 SDK installer dependency correction, before image or Renode data:**
Build 3529906 passed all WORK mount guards, installed Renode and the pinned
Zephyr/modules, and verified the SDK minimal archive checksum. SDK setup
then failed its CMake availability check: the pinned CMake wheel is in
`/opt/rtc-python/bin`, but the image `%environment` PATH does not apply to
`%post`. Add this venv directory to the build-time PATH. Inspection of the
same checksum-verified SDK archive's setup.sh shows unconditional checks
for CMake and wget using which; explicitly install wget and debianutils,
and check the three commands before later build steps. No runtime version
pin or selected input changes. Retain v6 logs; seal a separate v7 bundle
and use `tacc_work/20261022-v7`. No image was sealed or Renode simulation
run in v6; its afterok probe cannot execute after build failure.

**2026-10-22 runtime-configuration preservation, before any Renode simulation:**
Inspection of the checksum-verified Linux Renode archive showed that its
supplied runtimeconfig includes four configProperties. The earlier custom
launcher retained only two, omitting PredefinedCulturesOnly=false and
MetadataUpdater.IsSupported=false. Before testing, derive the external
.NET runtimeconfig directly from the supplied file, preserving every
property and changing only includedFrameworks (bundled 8.0.12) to framework
8.0.21 with rollForward=Disable, as required by the saved original version.
This avoids an unintended culture-handling difference. Pending build
3529922 was cancelled at zero elapsed time; v7 produced no image or data.
Seal v8 and use `tacc_work/20261022-v8`. All earlier SDK/PATH and WORK-mount
fixes remain; no frozen source, ELF, original record, clock schedule or
comparison rule changes. Source: Renode.runtimeconfig.json in the pinned
renode-1.17.0.linux-portable.tar.gz archive (SHA recorded above).

## 2026-10-12 Stage B deferred

The user closed the exploratory Stage B round as **deferred** because repeated Codex CLI connectivity timeouts interrupted the locked generation sequence. Do not run the proposed 12-call pilot or resume the 60-call round under this protocol. Retain the frozen prompts, call order, two completed sources, failed CLI and build attempts, nominal originals, and separately labeled access retries. The [condition-level interruption audit](../notes/STAGE_B_CALLBACK_INTERRUPTION_2026-10-12.md) remains part of the project record. Neither completed Stage B source enters any manuscript result, denominator, figure, table, or model/prompt comparison. The manuscript may describe the frozen design and the same-spec human packet solely as planned follow-up. Any future execution requires a new dated authorization and protocol amendment before generating or running tests.

## 2026-10-22 Phase 1 image identity checkpoint (no firmware runs)

The authorized v8 retry completed its sealed-input transfer and produced a
SIF in development build 3529954. Software inventory failed on Git's
container ownership guard; the dependent probe 3529956 was cancelled
without execution. Development inspection 3530002 used only a command-scoped
`git -c safe.directory=/opt/zephyrproject/zephyr` override, without account
or persistent Git configuration changes. Its records show a Renode version
string differing from the frozen plan: Linux build 20260907 and reported
.NET 8.0.12 versus saved local build 20260906 and reported .NET 8.0.21,
with the same f1dd1b4af source revision. External installed .NET is 8.0.21.
Version equivalence is not inferred from the shared source revision.
SIF SHA-256: `1f10025ee9d9b5e291c9d518ac65646c79e2f833886f96561c5259cb4c86d2b4`.

Stop before all firmware executions. Preserve image, logs, input bundle,
and original version/trace criteria. No changed scientific inputs, new
verdicts, resource-probe results, or calibration agreement are reported.
Any next execution must first resolve this image identity checkpoint;
no normal-queue submission is authorized. Source records:
`artifacts/tacc_phase1_20261022_v8/calibration_plan.json`
(`expected_renode_version`) and
`artifacts/tacc_phase1_20261022_v8/returned-slurm/inspect-3530002.out`.

## 2026-10-22 Approved Phase 1 environment resolution, before firmware data

The user authorizes official macOS ARM64 versus Linux portable release
packages as a disclosed environment difference, subject to exact calibration
verdicts and full raw trace-file hashes. Both checksum-verified official
v1.17.0 assets embed commit `f1dd1b4af7838b45a925c17603cdfed0a583844a`; their
build dates differ (20260906 / 20260907). The current GitHub v1.17.0 ref
resolves to `ab721d88e135a1bcb8ed2ecc5a38f51cbe61fdd2`, distinct from the
embedded asset revision. Do not rebuild from that moving ref or assert
bitwise cross-platform binary identity. Official release asset digests:
macOS `63b1fb691207f503cea937e4ec8fad3e068a517d0abac3c24c0206c62f6c4d12`;
Linux `4ba7c68b59e2447f188ef4b4b112fcccd2802582c460beedceb63b84e5605a5f`.
The mounted original Mac executable, Renode.dll, dependency/configuration
files and STM32F4 platform all match the checksum-verified macOS package.

Development diagnostic 3530040 shows that a runtimeconfig pin alone still
loads `/opt/renode/libcoreclr.so` from the bundled 8.0.12 runtimepack. Derive
a separate deps manifest removing only that runtimepack entry, so the
external, fixed 8.0.21 framework supplies runtime files. Preserve all other
dependencies, original manifest files, runtime configProperties, application
assemblies, toolchain, frozen ELFs, selected suites and frequencies. Test
the pin beside the application without executing firmware. Derive v9 from
the exact existing v8 SIF to avoid reinstalling packages; record both hashes.
The original local version remains in the plan alongside the exact expected
Linux execution version; this explicit approved difference is not an open
version allowlist. Fix only inventory's Git ownership check with a
command-scoped safe.directory option. Seal a new v9 bundle, retaining v8.

Proceed to the original one-run resource probe and, only on agreement,
packed development calibration. Any verdict, raw trace SHA-256, or
infrastructure error stops launches; do not normalize hashes or replace
failed results. Report all eight suites, with missing/unrun cells explicit.
Only complete exact agreement can be described as calibration-validated.
Stop for user approval before production. Source evidence is retained in
`notes/TACC_PHASE1_RENODE_PROVENANCE_2026-10-22.json` and the v8 returned
runtime host traces / development logs. No calibration result exists at
the time of this amendment.

The sealed v9 plan SHA-256 is
`e7fed249d4931344bbb022d4d63efec5435093cc1d7c92934de15f09ea00e0c9`.
Its 816 tasks, input hashes, selected suites, resource-probe choice and exact
comparison rule are identical to v8; only execution-environment metadata
and adapter/build code hashes differ.

## 2026-10-23 Phase 1 probe permission failure; execution stopped

The approved v9 image sealed with actual .NET 8.0.21 and SHA-256
`831dffc44d479a06ed7945a68bd746302319d2160edb19d731e3f0cd380d4239`.
Probe 3530050 then failed before adapter startup because the ordinary
container user could not open calibration.py (Permission denied). No
firmware verdicts or trace comparisons were generated. This is an
infrastructure failure, not a calibration mismatch or test failure.
Stop all further submissions; all eight suite comparisons remain unrun.
Preserve the failed v9 image and logs. A local correction is prepared to
normalize read/traverse permissions on the image's harness tree and check
adapter --help as the ordinary runtime user during sealing. Do not deploy
or submit a retry without new user authorization after this stop. No
ELF, source, original record, schedule, trace rule, model parameter or
paper result changes. Source: v9 returned-slurm/probe-3530050.out,
probe stdout/0.log, STOP.json, and returned-images/image.json.

## 2026-10-23 Standing Phase 1 infrastructure approval, before attempt v10

The user authorizes permission/path/bind/module/packaging corrections and
resubmissions on the development queue, without additional confirmation,
provided harness logic, sources, ELFs, frozen forecasts and existing records
remain byte-identical and before/after SHA-256 audits are logged. Stop after
three consecutive failed attempts. Conservatively count the prior v9 probe
permission failure as consecutive failure 1; no successful probe has reset
that counter. Any verdict or raw trace mismatch, required harness/test-input
change, completed calibration, or proposed normal-queue submission still
requires stopping for user approval. All credential and WORK-only rules
remain.

v10 applies only chmod -R a+rX to the container harness tree and an ordinary
user adapter --help check before sealing, as prepared after v9. The
calibration adapter, original simulator loop, resource logic, Launcher and
run wrapper are unchanged. The image remains derived from the same
checksum-verified v8 parent with the already approved .NET 8.0.21 pin. Use
a new v10 bundle and results directory; preserve v9 and its STOP marker.
Hash audits compare all protected tracked files and frozen calibration
inputs, and separately list the three permitted container-packaging changes.

v10 pre-execution audit: 29,634 protected files unchanged and all 1,755
sealed original input hashes match. Full before/after log is
`artifacts/tacc_phase1_20261023_v10/hash_audit.json` (SHA-256
`6d52e9179d54993ec4f49671825988b6f004c437a7974f1b52ff61f70e774ea5`).
Only build_image.sh and the two container definitions differ. The new
plan SHA-256 is
`aed1c266d9bbc2c962f57d882c4337ac3a7b1d3e2590c1ff29e453cb8e6d5e66`.

2026-10-23 v10 probe checkpoint: verdict and complete trace hash match.
The unchanged resource rule selects cap 32 and estimates 56.21 minutes for
the locked 816 cases, fitting the pre-existing 90-minute development job.
Proceed to packed calibration under standing approval. Full environment
validation remains pending all eight suite results; stop afterward.

## 2026-10-23 Phase 1 calibration-validated environment difference; STOP

The permission-only v10 fix passed ordinary-user readability and its
resource probe. Development job 3531436 then completed all eight suites,
102 saved cases per suite: **816/816 verdict agreements and 816/816 complete
raw trace-file SHA-256 agreements**, including 776 passes and 40 expected
assertion failures. No missing cases or mismatches. The original simulation
loop, adapter logic, source, ELF, forecasts and existing records were not
changed. The post-run audit confirms all 29,634 protected files unchanged.
The 32-worker packed run took 16:49 on one LS6 node; no Slurm array was used.

The official macOS ARM64 versus Linux x86_64 packages have different build
dates but the same embedded f1dd1b4af7838b45a925c17603cdfed0a583844a revision.
Both now use actual .NET 8.0.21. Record this as a **disclosed,
calibration-validated environment difference for the selected eight suites
and 816 saved cases**. It does not assert bitwise cross-platform package
identity or general emulator/silicon equivalence. The separately observed
current v1.17.0 ref difference remains disclosed in the provenance record.
SIF SHA-256:
`94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.

Evidence: `artifacts/tacc_phase1_20261023_v10/verified_calibration_report.json`
(SHA-256 `2ef964ac4a41fe13733f7aa4e33019536aaf29024f9cbfac0fa4708449c551ea`), returned raw records/traces,
`post_calibration_hash_verification.json` (SHA-256 `e7bbefcd71c8a074c1c1f94d8ca0b288b2ece084312920ebae2eeb03de18c428`), and
`slurm_accounting.txt`. The full per-suite table and prior failures/fixes
are retained in notes/TACC_PHASE1_STATUS_2026-10-22.md. These are calibration
reproduction checks, not additions to the original paper's denominators.

STOP after this report for explicit user approval. No production or normal
queue job has been submitted. Standing infrastructure approval does not
authorize a new scientific phase or bypass the next production approval.


## 2026-10-24 Phase 2 A–B prospective completion, before new execution

User approval follows the exact 816-case Phase 1 calibration. Measure only the
16 IDs in `analysis/rtc_threshold_sample_v2/sample.json`, field
`unsampled_prediction_only_run_ids`, using their unchanged original nominal
ELFs and sources from `results/rtc_timing_mutants_two_faults/manifest.json`.
Run the original shared 100 seeds and both exact legal endpoints: 1,632
primary cases. These IDs are all calendar-counting suites. Reuse the calibrated
Linux portable Renode image with actual .NET 8.0.21, SIF SHA-256
`94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.

Frozen forecasts, sample lock, saved platform bytes, test sources, ELFs, original
simulation implementation and old raw records stay unchanged. New adapters
bind sealed inputs and write exclusively to a new Phase 2 result directory.
Check protected-file hashes before and after. Do not fill the 12 historical
missing verdicts. No retries until pass: startup errors, timeouts and other
missing outcomes remain separately reported. Compare the 1,600 new seeded
verdicts with the original forecasts exactly by seed, not only by totals;
endpoints are separate measured challenges, not newly claimed frozen forecasts.
Report every mismatch without revising predictions. Replay each explicit
assertion failure in a fresh process and run the frozen task reference at
each distinct failing task/frequency, retaining unknown attribution pending
source, replay and reference evidence. Preserve the known raw tuple/list
comparison flag and independently audit persisted fields and raw trace hashes.

Normal queue, allocation TRA25006, one whole node, 32 Launcher workers with
memory capped at 80% using the Phase 1 resource allowance. Conservative primary
runtime: 120 + ceil(1632/32) * 83.4 * 1.5 = 6500.1 seconds, approximately
1.81 node-hours/SUs at one SU per node-hour. Request three hours (reservation
ceiling 3 SUs); additional failure replays/references consume that reservation
and never justify an unapproved additional job. Report node, Slurm ID, actual
Apptainer 1.4.1 version, image hash and plan hash in each record. Phase 3 must
present before/after numbers for approval before any manuscript change.

## 2026-10-24 Phase 2 D zero-fault controls, before new execution

After A–B, rebuild and nominally run the 66 eligible generated suites and three
upstream cases for each of three distinct disabled implementations: original
production RTC driver at 32 kHz (the shared disabled fast/slow oscillator
implementation); frozen `rtc_ll_stm32_quality.c` with every QUALITY switch and
delay explicitly zero (disabled nonarrival implementation); and frozen
`rtc_ll_stm32_alarm_offset.c` with QUALITY_ALARM_OFFSET_SIGN=0 (shared disabled
positive/negative offset implementation). No fault-driver source edits.
The two signed offsets share exactly the same zero variant and are not
misrepresented as two independent controls. Add three task references per
implementation: 207 primary controls plus nine reference controls = 216
build/run attempts. Offset-specific references use their frozen readback
sources; other references use the original reference triage sources.

Compile unchanged test sources/configurations with the pinned container
Zephyr commit and SDK. Preserve the board, overlays and supported alarm-mask
define. Record commands, macros, source/config/driver/overlay/build-log and new
ELF hashes; store new ELFs and logs only under the new D directory. Build
failures are distinct from selected-case assertion failures and infrastructure
missingness. Run each successful build once at nominal clock using the
unchanged quality simulator loop; no retries or substitutions. Report outcomes
by implementation, task, model and prompt, with references separate. Any
unexpected selected-case failure is retained and triggers a stop before repair
execution; it does not authorize modifying the harness or test inputs.

Use one normal-queue whole node, TRA25006, Launcher cap 16 and two compiler
workers per build. Reserve 4 GiB per worker under the same 80% memory ceiling.
A provisional estimate uses 300 seconds per build plus 125.1 seconds per run:
120 + ceil(216/16) * 425.1 = 6071.4 seconds (1.69 node-hours/SUs); build time is
an allowance, not a measured throughput claim. Request four hours (reservation
ceiling 4 SUs). Confirm and report this estimate at submission. No repairs or
LLM repair generation is authorized by this control job.


## 2026-10-24 E mechanical repair study: registration for approval, before variants

Status: protocol and six review-only example sources may be prepared now;
**no E compilation, simulation, or E2 model calls before explicit user approval**.
D must first disclose any disabled-control failures or missingness. A–B and D
remain separate new-data phases. This amendment is written before any repair
variant source is created and before any repair outcome is observed.

### Subjects and immutable V0

Include the 30 generated suites with a nonempty `clock_only_budget_s` in the
existing `analysis/rtc_padding_audit.csv`, plus the three selected upstream
RTC cases: **33 subjects (27 generated counting, three generated pending,
one upstream callback, one upstream pending, one upstream counting)**.
This is the pre-existing scalar-budget subset, not every source containing
a sleep. There is no eligible generated callback in this subset. The exact
roster, original source/ELF SHA-256 and budget expressions are sealed in
`notes/repair_review_2026-10-24/subjects.json`. V0 uses those unchanged source
and ELF bytes, with all new runs written separately; old results are preserved.

| Subject | Existing budget (s) |
|---|---:|
| `astra-range_absent-rtc_alarm_pending-r05` | 15 |
| `astra-range_absent-rtc_time_counting-r01` | 40 |
| `astra-range_absent-rtc_time_counting-r02` | 40 |
| `astra-range_absent-rtc_time_counting-r03` | 60 |
| `astra-range_absent-rtc_time_counting-r04` | 60 |
| `astra-range_absent-rtc_time_counting-r05` | 60 |
| `astra-range_present-rtc_time_counting-r01` | 20 |
| `astra-range_present-rtc_time_counting-r02` | 30 |
| `astra-range_present-rtc_time_counting-r03` | 20 |
| `astra-range_present-rtc_time_counting-r04` | 24 |
| `astra-range_present-rtc_time_counting-r05` | 20 |
| `luna-range_absent-rtc_time_counting-r01` | 20 |
| `luna-range_absent-rtc_time_counting-r02` | 30 |
| `luna-range_absent-rtc_time_counting-r03` | 20 |
| `luna-range_absent-rtc_time_counting-r05` | 30 |
| `luna-range_present-rtc_time_counting-r01` | 60 |
| `luna-range_present-rtc_time_counting-r02` | 60 |
| `luna-range_present-rtc_time_counting-r03` | 60 |
| `sol-range_absent-rtc_alarm_pending-r01` | 16 |
| `sol-range_absent-rtc_alarm_pending-r03` | 15 |
| `sol-range_absent-rtc_time_counting-r01` | 60 |
| `sol-range_absent-rtc_time_counting-r02` | 30 |
| `sol-range_absent-rtc_time_counting-r03` | 45 |
| `sol-range_absent-rtc_time_counting-r04` | 25 |
| `sol-range_absent-rtc_time_counting-r05` | 30 |
| `sol-range_present-rtc_time_counting-r01` | 40 |
| `sol-range_present-rtc_time_counting-r02` | 30 |
| `sol-range_present-rtc_time_counting-r03` | 30 |
| `sol-range_present-rtc_time_counting-r04` | 40 |
| `sol-range_present-rtc_time_counting-r05` | 30 |
| `human-rtc_alarm_callback` | 13 |
| `human-rtc_alarm_pending` | 13 |
| `human-rtc_time_counting` | 14.5 |

### Shared transformation rules

Use **20,824 ms = 18.824 s + 2 s** as the observation ceiling, measured by
kernel uptime from immediately before the successful `rtc_set_time` that
starts each target observation. Each reset/repetition gets its own ceiling.
This follows the requested ideal ten-RTC-second slow bound plus a fixed
experimental margin; it is not a measured bound on interrupt delivery.

V1 is a **deadline normalization**, not extension-only: an original wait over
20,824 ms is shortened. Thus normalization can remove over-padding as well as
extend brittle short waits. Record each original/new budget and direction.
Do not silently use max(original, new). This explicit interpretation and the
six examples require the user's approval before E execution.

Preserve all original target calendars, alarm channels, supported masks,
board/driver/clock configuration, setup, teardown, and non-time assertions.
Keep each original zassert invocation, except a timeout's numeric/loop-limit
expression may be redirected to the normalized deadline. Preserve original
success predicates, including any original exact equality, and record any
additional V3 predicate separately. A source with a poll counter retains its
counter variable for assertions but replaces the counter timeout with an
absolute uptime deadline. Clamp each sleep to nonnegative remaining time;
never add another full observation ceiling after a partial wait. Existing
pre-arrival checks stay at their original early observation points. For a
multi-stage calendar/pending path, its service stage uses min(original service
allowance, remaining common deadline); no fresh 3-second extension beyond
20,824 ms. No asserted failure is repaired again after outcomes are seen.

### V1: deadline normalization only

Replace the scalar timeout identified by the roster's existing budget
expression with the common ceiling. Retain the existing fixed-sleep versus
polling strategy and its original polling cadence, and retain original break
conditions. Where an upstream alarm uses 3 seconds plus 10 seconds, retain the
3-second early check and replace the second fixed sleep with the remaining
portion of the common ceiling. Timer anchors precede the initial/reset
rtc_set_time. A later pending service wait shares that deadline as above.
No new configuration or calendar assertions in V1.

### V2: event/state waiting with the same ceiling

Start from V1. Replace the final fixed observation sleep with waiting for the
existing completion predicate (all requested callback bits, pending state,
or the original calendar progress condition) under the same common ceiling.
Use the original protected callback flags, observed through 20-ms sleeps;
no unprotected callback state. Already state-polling tests retain their
predicate and switch to 20-ms polling. This may be only a cadence change for
some subjects; label it accordingly, not as a new event primitive. Retain all
original checks before and after the wait. A destructive pending read is
latched and substituted at the original consuming assertion so the observation
is not accidentally cleared twice. Do not add a new oracle in V2.

### V3: V2 plus the frozen task's required checks

For callbacks, read back configured supported alarm fields/mask, capture
RTC year/month/day/hour/minute/second in each callback before atomically
publishing completion, and check successful reads, configured channel identity,
not-before and exact requested calendar second in the test thread. Store
callback errors/invalid IDs without out-of-bounds indexing or ISR assertions.
Keep the original flags and assertions. Add only missing checks; already
present checks are not duplicated. Each repetition clears capture/error state
before enabling/observing the next event.

For pending, require successful configuration and readback of supported alarm
fields/mask; successful RTC reads bracketing the pending observation; no pending
state before target; and pending observed at/after target under the shared
ceiling. A pending event's recorded RTC calendar must be at/after target.
**Do not invent an exact/upper calendar bound for pending**: its frozen spec
requires eventual pending after target, not exact-second callback delivery.
For counting, require successful set and initial read, nondecreasing successive
calendar observations, and at least ten RTC seconds of progress crossing the
configured year boundary. Keep any stronger original equality unchanged.
Use full calendar comparison/epoch conversion, not tm_sec alone. Configuration
readback detects compare programming; callback timestamp equality also tests
delivery precision within this simulator. Neither supplies an independent
oscillator reference or guarantees detection of a fast oscillator.

Apply these rules only at the source sites identified by the existing budget
expressions. Before full generation, freeze a per-source patch-site ledger
and diff against V0. If a source cannot be transformed without changing
unrelated logic, retain it as not applicable and report why; do not improvise
a different repair. Example artifacts show one upstream callback and one
Sol base pending source for each V1, V2 and V3. They are source previews,
not compiled or validated experimental variants.

### Outcome measures and run policy (execution requires approval)

For each V0/V1/V2/V3 subject, report nominal/build status, legal-clock failure
counts and full per-setting vectors on the original 100 seeds plus both
endpoints, with missing outcomes separate. Reuse frozen V0 ELF bytes; build
new variant ELFs only in separate directories and record source/config/build
command/ELF hashes. Do not alter original forecasts or apply them to variants.
Each variant first clears a build and five-launch nominal gate; a failed
gate remains a failed repair attempt and does not get iterated until passing.

Challenge evaluable variants with fast/slow oscillator and driver-path
nonarrival operators, and signed one-RTC-second alarm offsets for alarm
subjects. Counting signed-offset challenges are non-activation controls,
outside the alarm denominator. A fault detection requires verified activation
and explicit selected-case failure. Gate losses are retained in all-attempt
repair yields. Use the same protected-input audits, separate disabled controls,
original selected-case parsing, assertion replay and task references as A–B.
Report virtual duration and host wall time separately; compare legal survival
and each fault separately, not a single pooled mutation score. Show results
per subject/task and variant, plus a survival versus slow-detection table.
All results are exploratory/post-result repairs, not prospective model evidence.

There are 33 x 4 x 102 = 13,464 planned legal-clock slots before any gate
attrition, 396 fast/slow/nonarrival slots, 40 activated-alarm-offset slots,
and 224 optional counting offset-control slots. Nominal gates, replays and
references are additional and must be included in a runtime/SU proposal before
submission. E2 remains deferred until the user approves E results. Phase 3
must show old/new numbers and their source files before any paper edit.


## 2026-10-24 E revision approved before any repair builds or runs: split V1

The user approves the 33-subject repair study and execution without another
approval stop, with this revision made before any repair compilation or run.
The original review-only previews remain preserved; they are not outcomes.
The 2026-10-24 E subject roster, V0 bytes, V2/V3 semantics, gates, fault
criteria, missingness policy and Phase 3 paper-approval checkpoint stay fixed.
E2 remains on hold until the user approves the E results.

- **V1 (naive extension):** new scalar wait is
  max(original scalar wait, 20,824 ms). Never shorten an existing wait.
  If the original wait is already at least 20,824 ms, retain its original
  source/deadline semantics exactly; report V1 as a no-op for that subject.
  Otherwise apply the prior deadline-normalization transformation at 20,824 ms.
- **V1b (right-sized fixed wait):** new scalar wait is exactly 20,824 ms;
  this is the previously previewed V1 behavior. Retain original wait style
  and polling cadence with the shared ceiling and original early checks.
- **V2:** unchanged from the prior amendment; derives from V1b, not the new
  extension-only V1. Use event/state waiting and 20-ms polling with the same
  20,824-ms ceiling, retaining original assertions.
- **V3:** unchanged from the prior amendment; V2 plus only the frozen task's
  missing configuration/calendar/identity checks. No invented exact upper
  calendar bound for pending. When the source already implements all required
  task checks, record V3 as unchanged from V2 rather than duplicate assertions.

Before any build, show V1/V1b versus frozen V0 for the same upstream callback
and Sol base pending r03 examples, plus Sol base counting r01 (original scalar
budget 60 seconds). The latter V1 is deliberately unchanged; V1b reduces its
budget to 20,824 ms. Source-site and assertion-retention checks are frozen
before generating the full cohort. Original non-time assertions and all
frozen source/ELF/forecast/results remain unchanged on disk.

Evaluate V0, V1, V1b, V2 and V3 for all 33 subjects, with losses retained.
The revised pre-attrition denominators are 33 x 5 x 102 = **16,830** legal-clock
slots, **825** five-launch nominal-gate slots, **495** fast/slow/nonarrival
slots and **50** activated signed-alarm-offset slots. Counting offset controls
are non-activation checks, outside the alarm denominator, and may be omitted
as the prior amendment made them optional. Explicit assertion failures need
fresh-process replay and task-reference checks at distinct failing settings.
Do not rerun the 12 historical missing cases. Use new output directories only.

A–B then D execution order remains in force. Disclose D failures/missingness
before E fault evaluation; an unexpected control failure must be investigated
without modifying frozen harness logic or inputs. Report E job/node/wall-time
and SU estimates at submission under this explicit execution approval. New
variant generation/build orchestration may be added separately; do not edit
the calibrated simulation implementation. Before paper edits, stop with the
Phase 3 old/new number table and source records.


### 2026-10-24 E V1 service-stage clarification, before builds/runs

For the naive-extension V1, retain each existing post-calendar service
allowance unchanged. In particular Sol base pending r03 retains its separate
3-second pending-service wait after extending the first scalar calendar
budget to max(15, 20.824) seconds. Its total possible duration can therefore
reach 23.824 seconds; report that stage allowance separately. Capping this
existing service wait would contradict the user's instruction never to
shorten an existing wait. V1b, V2 and V3 retain the previously registered
single 20.824-second overall ceiling and clamp that service stage to remaining
time. Other already-long V1 sources remain byte-identical to V0. This is a
pre-run operational clarification of the approved split, not an outcome-based
repair. The six updated V1/V1b diffs will expose it before compilation.


## 2026-10-24 Phase 2 compiler-cache infrastructure correction, before E builds

D job 3532338 encountered a common build-environment failure: pinned Zephyr
attempted writes beneath `/opt/zephyrproject/zephyr/.cache` inside the read-only
SIF. Two independently inspected initial build logs show this same compiler
capability-cache error. These are infrastructure build losses, not selected
ztest assertion failures or evidence against a source. The attempt was
cancelled and its existing logs/build records remain preserved in D v1.
Unstarted E jobs 3532458 and 3532464 were cancelled before any repair build/run.
Do not substitute successful retries into those original failed records.

Under the standing infrastructure-only development-queue authorization,
validate a path-only fix in a new D v2 bundle/results directory. Set explicit
container XDG_CACHE_HOME=/var/tmp using APPTAINERENV_XDG_CACHE_HOME; /var/tmp is
already bound to a private per-task runtime/work directory under WORK.
Pinned `cmake/modules/user_cache.cmake` prefers this writable cache location.
No SIF rebuild, firmware source change, driver modification, compiler flag
change, frozen ELF change, forecast change, or simulation-loop change.
Both the original D Python worker and original E build/simulation adapters
remain byte-identical; new shell packaging wrappers only set the cache path
and allow development execution for the D retry.

D v2 keeps the exact 216-task roster, source/config/driver hashes and frozen
simulation hashes. Its new plan SHA-256 is
61b8715bce7400dc5a380599731f970d8657defb946584875973cdfde81e6518.
Run task 0 once, confirm its successful build and nominal pass, then pack
only tasks 1..215. If that first control fails, stop before launching the
remainder. Report the actual development partition in every record. Source
and raw-result immutability checks precede and follow the fix; count the
cancelled D job as infrastructure attempt 1. Stop after three consecutive
failed infrastructure attempts; any required simulation/test-input change
still requires separate approval. After complete passing D controls, restore
the already-approved E normal jobs with the same scientific plan and sealed
source cohort, using the validated cache environment. E2 stays held and
Phase 3 must precede any paper edits.


## 2026-10-25 S1 subject and board survey, before any expansion runs

Scope: read-only inventory at pinned Zephyr commit
3568e1b6d5cdd51a6b964a2a1d6d29200fea2056 and calibrated Renode release
source f1dd1b4af7838b45a925c17603cdfed0a583844a. Enumerate individual
ZTEST/ZTEST_USER cases, including conditional cases and documented skips,
in the RTC application, all watchdog applications and STM32-RTC-capable
counter applications. Distinguish existing build evidence, static
configuration feasibility, platform exclusions and unverified builds. S1
does not compile firmware or execute Renode. Model presence is distinct
from validation of the peripheral's behavior, reset path or clock coupling.

Survey every board DTS target that resolves to an STM32 SoC, including
third-party vendors, using source inclusion and devicetree preprocessing
where feasible. Count resolved RTC source selections and enabled IWDG/LSI
configuration per DTS target; also report unique board directories, disabled
peripherals, unresolved targets and explicit versus inherited settings.
Do not infer clock frequency distributions from datasheet extrema. Verify
ST document titles/numbers/URLs and record the conditions for each range.

Save scripts, case-level CSV, board-target CSV, model evidence, source hashes
and a proposed run-count/SU ledger in new survey directories. Estimates are
planning assumptions, not approved jobs or measured feasibility results.
Record protected-file hash checks before/after. E evaluation job 3532543 is
left untouched; E2 remains held. Stop after S1 for subject/board approval.
No S2 runs, S3 coverage executions or S4 model generations are authorized
by this survey registration. No manuscript changes in S1.


## 2026-10-25 S2 qualification registration, before new builds or runs

Authorization: S1 reviewed; the user approved qualification only, followed by a
mandatory stop before production. E job 3532543 is untouched and E2 stays held.
No paper changes are authorized in this qualification step.

Subjects: every case in the pinned RTC API application, counter basic API in a
non-stock RTC-only configuration, and counter seconds if it builds. No test C
source or assertion changes. Preserve all capability skips as skips. Enable the
RTC alarm, update and calibration test compilation paths; unsupported APIs may
skip. Counter builds select COUNTER_RTC_STM32, disable RTC API and STM32 timer
counters, keep SUBSECONDS disabled, supply rtc0/rtc-0 aliases, and explicitly
suppress auto-loaded stock board test overlays. This is a non-stock device
selection, not an unmodified stock-board run, and must be disclosed in the paper.

Boards: stm32f4_disco, nucleo_f767zi, stm32f746g_disco and nucleo_h753zi.
stm32f072b_disco is conditional on documenting actual generated devicetree and
unmodified driver divider behavior; stm32h747i_disco is excluded. F4 retains
its existing HSI system-clock overlay, while new boards initially retain their
stock system clock. Renode CPU PerformanceInMips remains 16; capture SysTick
configuration and RTC prescalers in calibration records. No model implementation
or driver source is changed to obtain qualification.

Freeze datasheet clock inputs: F407/F767/F746 17000..47000 Hz, nominal 32000;
H753 DS12117 Rev 10, revision V envelope, VDD 1.62..3.6 V and TJ -40..105 C,
29760..33600 Hz, nominal 32000. This is a simulated revision-V input envelope,
not evidence of a physical chip revision; record the model's DBGMCU response
separately without changing it. F072 DS9826 Rev 6 uses 30000..50000 Hz,
nominal 40000, VDDA 3.3 V and TA -40..105 C. Do not adjust prescalers or test
waits to force a nominal pass. The RTC API driver defaults to 128*250 even on
F0 with LSI; the counter driver computes its synchronous divider from
STM32_LSI_FREQ (the DT clock frequency), yielding 128*312=39936 at 40000 Hz
when no prescaler override exists. Qualification must confirm these source
expectations against generated DTS and programmed PRER. If unresolved, omit F072.

Before production, each build has five fresh nominal launches followed by seven
calibration settings: both endpoints and saved schedule seeds 0..4. The F4
schedule is copied exactly from the frozen original; other ranges use the same
seed algorithm random.Random(seed).randint(min,max), with the resulting full
100-entry list sealed before execution. No production schedule runs are
submitted at this checkpoint. Calibration assertion failures at legal endpoints
are legitimate outcomes and are not automatically infrastructure failures.
Nominal qualification is per case: five explicit passes qualify; persistent
capability skips, nominal failures and missing cases remain separate. Run all
cases in each application, without deleting failing or skipped cases. Unknown
or absent verdicts are never recoded as passes. Require a completed application
marker and one verdict per compiled expected case, or retain missingness.

Measure a single first nominal launch on a development compute node, then choose
packed run concurrency <= min(32, CPUs, floor(0.80*MemAvailable/(1.5*peakRSS))).
Build concurrency initially <=4, with two compiler workers per build. Each
Launcher jobfile line is one application/configuration/clock launch, with one
Apptainer exec. All jobs use development and -A TRA25006, pinned
 tacc-apptainer/1.4.1 and launcher/3.10, the calibrated SIF hash
94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1.
Record node, job ID, image hash, Apptainer version, inputs, elapsed time and peak
RSS. New output directories only. Read-only upstream and container mounts;
private compiler caches/home/tmp and outputs are WORK-backed. Remote code
updates use git pull only. Protected hashes before and after every attempt;
retain all failed attempts. Infrastructure-only recovery is capped at three
attempts and must not change test C, drivers, frozen inputs or old records.

Watchdog is a separate bounded development qualification on F4 and H753 only:
unchanged full wdt_basic_api application, IWDG-only overlay and explicit
WDT_DISABLE_AT_BOOT=y (the prior separately registered configuration). One
nominal 120-virtual-second/600-wall-second launch per board must show multiple
suite starts/reboot progression and explicit selected-case completion; a mere
wait-for-reset message is insufficient. Record failures and exclude if not
qualified. At most three attempts, only for demonstrated infrastructure fixes;
no semantic retry-until-pass, driver patches, reset injection or application
changes. No watchdog production is approved by successful qualification alone.

Report results per case and board, including all skips and missing outcomes.
Do not pool board replicas as independent tests. Production reports lead with
source-derived frequency boundaries and source-line/wait explanations, which
must be tied to each board's actual divider. Prepare final run counts and SU
estimates from measured resource usage, then STOP for approval before any
normal-queue submission. Keep S1 board counts (106 LSI / 40 LSE RTC targets)
and verified AN5067, AN5126 and RM0090 evidence unchanged for later paper work.

### S2 pre-run configuration clarification, 2026-10-25

The full RTC application explicitly retains TEST_RTC_ALARM_TIME_MASK=7,
matching the existing selected upstream configuration in
subjects/phase1_lsi_rtc/rtc_alarm.conf. Its stock Kconfig default is 6;
we disclose the seconds/minutes/hours mask and added update/calibration
compilation switches instead of calling this a stock default configuration.
RTC/counter test source, assertions and driver bytes remain unchanged.
Each generic board launch reuses the frozen monitor adapter's command and
RunFor operations but omits its hardcoded F4 LED/GPIO startup read, which
is unrelated to RTC and invalid on F0/H7. This is a new board adapter,
not a modification of the old calibrated harness. Log its sealed hash.
The F072 conditional check preserves each driver's own default divider;
no compensating prescaler overlay is applied. Runtime capture and generated
DTS review must verify source-derived expectations before any admission.

### S2 infrastructure amendment, 2026-10-25, before any firmware launch

Development job 3533587 completed all 17 builds but stopped at the first
Renode --version check, before a firmware launch. The new preparation script
mistakenly copied the historical macOS 20260906 build string instead of the
already approved/calibrated Linux 20260907 string. Both are v1.17.0,
f1dd1b4af, .NET 8.0.21, as documented in the Phase 1 status/provenance.
Pin the new bundle to the exact Linux string from the existing v10
software-inventory.json, retaining the local string as provenance. The SIF,
simulation/build worker, test C, drivers, schedules, overlays and configs do
not change. In a new output namespace on development, verify and copy all 17
build records, logs, generated DTS/config snapshots and ELFs byte-for-byte;
record each before/after hash and original build job. Do not rebuild or edit
those ELFs, replace failed artifacts or modify the first attempt. Re-run only
the not-yet-executed resource probe, then continue qualification if successful.
This is a packaging metadata correction under the approved infrastructure
recovery rule, not a relaxed version gate or changed experiment.

## 2026-10-26 S2 reviewed exclusions and calibration continuation, before new runs

Authorization: the user reviewed S2 qualification, approved the exclusions below,
approved finishing exactly fifteen interrupted/unstarted calibration settings
unchanged on development, and conditionally approved normal-queue production
only after every setting completes without harness errors or unexpected failures.
E evaluation 3532543 may be inspected read-only; E2 and manuscript edits remain
held. No configuration or source repair is authorized by this amendment.

Evidence: results/s2_qualification_20261025_v1/evidence_v1.tar.gz, SHA-256
be4c26e901f65bddfb0319bca2d0f94c380d76c9b74f84bf81749ce5feaa85f2;
analysis/s2_qualification_20261026_v2 contains the derived per-case checkpoint.
Exclusions, without modifying configurations:
- stm32f746g_disco counter_basic_api: all five nominal applications end without
  complete case summaries after an MPU data-access fault in the second suite
  (test_set_top_value_without_alarm); preceding UART reports partition-slot
  exhaustion. Evidence: raw/uart/f746-counter-nominal-085.log through -089.log.
  Partial individual case lines do not qualify the complete application.
  Keep this board's RTC API and counter_seconds configurations if all gates pass.
- stm32f072b_disco entirely: all fifteen nominal launches have no test UART
  output or application completion. Evidence: raw/uart/f072-rtc-nominal-146.log
  through -150.log, f072-counter-nominal-158.log through -162.log, and
  f072-seconds-nominal-170.log through -174.log, with matching monitor/records.
  Its runtime RTC divider observation is unconfirmed and must not be reported
  as a hardware/driver finding. Static DTS/source expectations are not runtime
  confirmation and this board supplies no experiment verdicts.
- F4/H753 watchdog: each bounded probe reaches 120 simulated seconds, shows one
  reset request and no reboot or completed case. Evidence: raw/uart and records
  f4-wdt-nominal-036 and h753-wdt-nominal-145. No further watchdog attempts.

Resume task indices from the unchanged v4 schedule:
18,19,21,55,56,58,71,72,79,119,120,127,140,141,143.
The six interrupted originals remain missing in their original directory; the
nine unstarted settings remain documented as unstarted there. New attempts use
a distinct bundle/output namespace, with explicit linkage to those originals.
Reuse verified ELFs, source, configuration, complete task roster, frequencies,
Renode input platforms, original cache bytes, original simulation worker and
per-run virtual/wall limits unchanged. Only scheduling/namespace/provenance
metadata changes. Copy/audit builds on a compute node, with no rebuild.
Use the development QoS maximum 02:00:00 (queried 2026-10-26), one node,
-A TRA25006, pinned tacc-apptainer/1.4.1 and launcher/3.10. Pack fifteen task
lines with fifteen workers, one task per worker, rather than sequential stages
or interleaving several long runs on a worker. Existing per-run wall limits
are at most 1800 seconds, within the two-hour allocation. The provisional
expected cost is about 0.5 SU and reservation ceiling is 2 SU; whole-node
billing and minimum charges apply. Protected hashes before/after and separate
attempt logs remain mandatory. Stop on authentication problems or three
consecutive infrastructure failures; no scientific-input change is permitted.

Freeze the qualification acceptance rule before these attempts:
- F4/F767 counter at 47000,44670,45282 Hz: complete application; the same four
  nominal runnable cases pass and seven capability cases skip.
- F767 counter_seconds at 24797 and 24734 Hz: an explicit lower-bound failure
  at main.c:41 (elapsed >= MIN_BOUND) is expected, matching existing F4/F746
  qualification at identical frequencies/dividers. This is an anticipated
  legal-clock assertion failure, not an infrastructure failure.
- F746 RTC at 47000 Hz and H753 RTC at 30734,30726 Hz: five passes, update
  callback and Y2K capability skips, complete applications.
- H753 counter at 33600 Hz: the same three nominal runnable cases pass and
  eight capability cases skip. H753 counter_seconds at 33218,30310,30734 Hz pass.
Require the exact per-case vectors above, completed application markers,
unique expected case summaries, matching hashes/runtime, no harness error,
and explicit evidence for the two anticipated failures. Any different verdict,
missing case, new error or unexpected capability change blocks production and
must be reported. These are newly frozen continuation checks, not alterations
of the original forecasts or extra evidence for their accuracy.

Conditional final cohort: F4 RTC API/counter basic/counter seconds; F767 RTC
API/counter basic/counter seconds; F746 RTC API/counter seconds; H753 RTC
API/counter basic/counter seconds. Every declared case stays in each application,
including capability skips. The non-stock RTC-only/no-subsecond counter
selection and RTC mask 7 remain disclosed. Each qualified configuration gets
100 saved legal settings plus endpoints, 102 launches, total 1122 launches
and 6630 declared case-verdict slots, including skips. Never pool board replicas
as independent tests. Baseline runnable/skipped counts: F4 10/9, F767 10/9,
F746 6/2 across its retained eight cases, H753 9/10; report per-application
counts and dynamic skips separately. These counts are conditional on the
fifteen acceptance checks, not preassigned production outcomes.

After acceptance, freeze a new production plan with exactly these reused ELFs,
configurations, board-specific schedules and the same simulation function.
A separate outer adapter may admit the normal partition and record its actual
partition/job metadata; it must not spoof development or alter the frozen
worker's simulation/test behavior. Pin the verified F7 SVD bytes returned from
qualification for offline production use, with a disclosed cache-packaging
change; compare source/ELF/platform hashes before/after. Report job IDs and SUs
at submission. Current primary-only planning estimate is 4.48 SU at 32 workers
with a 1.5 allowance; provision one normal node for six hours (6-SU reservation
ceiling), subject to updated returned calibration runtimes. This conditional
approval does not authorize a submission if any acceptance check fails.
Missing production outcomes stay missing; no silent diagnostic substitution.
Replays and reference attribution follow the existing protocol in separate new
namespaces. E2 and paper changes remain held, including after submission.

## 2026-10-26 scheduling-only E resubmission and checkout recovery verification

The user authorized one preservation-first exception to git-pull-only recovery.
All 28 checkout collisions matched origin/main before recovery. Backed up/hash
logged all files under WORK/tacc_work/20261026-git-checkout-recovery-v1, moved
only the 26 untracked collisions, restored only DESIGN.md and the S2 status
note to the former HEAD, then pulled. LS6 and Mac both reached
abff0ced99983e9b3f60dc35ee5209c8a065f831; all 28 pulled hashes match the retained
backup, LS6 git status is clean and the protected audit reports 30,067 unchanged
files (audit SHA 7a8bfb74eca3008823a06bf6ffc9824ac518d078ac8241d579ab1b1445446ede).
S2 simulation/packing core hashes are unchanged. Keep the WORK backup.
The fifteen-setting continuation is re-sealed in an unused metadata namespace
only to include this updated DESIGN hash and additional offline-report code;
its task roster, scientific inputs, original worker and all run limits remain
unchanged. Earlier unsubmitted seals are retained, not experiment attempts.

The user also authorized replacing E evaluation 3532543 with a 12-hour normal
allocation if it remains pending. The read-only check still showed PENDING,
Priority, no start, with 18-hour limit. Before cancelling, recheck pending state
and no evaluation/control outputs. Cancel only in PENDING state; if it starts,
leave it running and do not create a duplicate. Reuse the completed gate job
3532542, sealed execution/ELF manifest, existing E protocol, tasks and per-run
limits unchanged. No gate rebuilds or nominal reruns. Submit the same controls
and evaluation stages with -A TRA25006, one node, normal, 12:00:00, cap32,
tacc-apptainer/1.4.1 and launcher/3.10. The prior expected cost is 8 SU; new
reservation ceiling is 12 SU. Preserve old submission/cancellation evidence,
new receipt, and all hashes. An unstarted pending job contributes no firmware
verdicts. New control/evaluation raw directories must not replace existing
records. This changes the Slurm allocation limit, not test observation bounds.
E2 and paper edits stay held. S2 production remains conditional on all fifteen
registered continuation checks, independently of E scheduling.


## 2026-10-31 Storage recovery and S2 priority, before new follow-up execution

The user requires WORK quota usage below 700,000 files before resuming E and
prioritizes S2 for Progress Report 2 around November 7. Restore headroom, then
collect and verify S2 primary evidence and finish S2 replay/reference
attribution before auditing/resuming E. E2 and manuscript changes remain held.

Only closed, unprotected outputs may be pruned after an archive on WORK has
exact member coverage and matching extracted-content hashes. Preserve the
archive hash and verification manifest before deleting any loose original.
Original factorial records in the immutable protection ledger stay loose;
archiving does not waive protection. Preserve all frozen sources, forecasts,
ELFs, build logs, recorded hashes and the checkout-recovery backup. Build
cleanup removes only regenerable intermediates with per-unit checkpoints and
retained-file/input/protection checks. Missing scientific verdicts stay missing.

New jobs use the storage contract in harness/tacc_storage/: build trees and
loose run output on SCRATCH; per-task container homes/caches/temporary files on
node-local /tmp; checksummed final archives and manifests on WORK. The frozen
legacy WORK-writing wrappers are retained but must not be invoked for future
follow-ups. A storage bind may preserve a locked worker's logical output
paths, while its physical new output remains separate from original records.
Record that mapping plus actual node, job ID, container hash, Apptainer version
and pinned modules. Pack outputs before publishing to WORK, including a
documented interruption path; final evidence must not remain only on SCRATCH.
No original harness logic, test source, ELF, forecast or record changes.

S2 evidence collection continues to use the original collector and selection
logic. Validate primary evidence against the registered DESIGN snapshot that
its plan seals, not a subsequently appended amendment. The snapshot is a
read-only protocol view; the current amendment log is not reset or overwritten.
Replays use identical full-application inputs and the original simulation
function in fresh processes, in a new namespace. A single application replay
may cover several failing cases; compare each case separately and preserve
capability skips. Reference artifacts and task lists must be frozen before
reference builds/runs. Passing a reference alone does not establish brittle
behavior when it omits an original rate contract or when an earlier case can
cause later shared-state failure. Keep those explanations unresolved unless
the source, trace and reference evidence establish the attribution.

Normal replay/reference submissions still require the job, nodes, wall time
and estimated SUs to be reported and approved under the standing rules. No
new S2 follow-up run or E recovery run is authorized by a storage fix alone.
The separate E amendment and exact incomplete/not-started index list will be
recorded only after S2, before any E retry. Completed records and finalized
harness-error missing verdicts will not be rerun.

Storage implementation clarification, 2026-10-31, before archival pruning:
The completed D-v2 output can be archived in full, including generated build
headers/link copies, before pruning its regenerable build products. Pin all
216 build-record hashes to the previously verified D evidence archive and
verify historical ELF/log hashes before pruning. Keep configurations, DTS,
metadata, app inputs, ELFs and logs loose. Never prune a protected/sealed input
path. Regenerated headers within build/ are not the original test sources;
the verified archive retains their bytes or link metadata. The closed D
private runtime/cache tree is separately archived and verified before pruning.
E's partial verdict directories and the checkout recovery backup are excluded.

## 2026-10-31 S2 evidence-return infrastructure rerun, before resubmission

WORK read 686,770 files (`lfs quota`) after cleanup jobs 3544396, 3544417 and
3544463 completed, below the 700,000 gate. User decision of 2026-10-31: the
700,000 target gates E only; S2 evidence and replays may proceed below 920,000
with SCRATCH/node-local outputs and archive-only WORK publication. Both gates
currently pass, so no gate code changes.

S2 evidence-return job 3544434 (adapter `s2_archive_scratch.py`, SHA-256
`95c8f79e53272093df6f639ebdb6ff1fce4fa5ed91c584f54ddd696c34104385`) failed
with exit 127 after 1:23. Its headroom gate passed (686,766) and its staging
audit verified all 30,067 protected files unchanged. The collector never
started: the inner `bash -l -c` set `set -u` before `module load
tacc-apptainer/1.4.1`, whose bash-completion references unbound
`BASH_COMPLETION_DEBUG`. The failure was reproduced on a login node and the
fix there ran with exit 0. This is an infrastructure failure. No collector
output, firmware run or original record was produced or changed. Its SCRATCH
report and two WORK staging receipts under
`tacc_work/20261031-s2-return-3544434/` are retained.

Rerun once under a new tag with
`notes/quota_recovery_2026-10-31/s2_archive_scratch_v2.py` (SHA-256
`891054aebdfaf8d00e29d10e90cab456fb1de9b51ee30f3288b519b0f409b2a0`). The only
functional change is `set +u` / `set -u` around the two module loads, matching
`harness/tacc_storage/runtime.sh`. The collector, selection code, sealed
plan/SIF hashes, historical DESIGN snapshot (`ea7ab441`), command list,
verification and WORK publication are unchanged. Use the development queue,
one node, 02:00:00, TRA25006, and no dependency. The S2 production
simulations (job 3535524) are not rerun. No new builds or simulations are
run. The earlier conditional replay plan stays unfrozen until this archive is
returned and its coverage, checksums, ELF and logs are independently verified.

## 2026-11-01 S2 archive verified, replay roster frozen, storage check before replays

S2 evidence-return job 3544535 COMPLETED (exit 0, 8:08) with no new builds or
simulations. Its archive, SHA-256
`0de8c18ebabe0dd8e91b4df43072dbd1aa5843e1455f455831afbf00d951d85e`, was
transferred and independently verified on the Mac with the unchanged
`verify_returned.py` and `audit_primary.py`: 9,117 manifest files, source
copies, protected before/after (30,067 unchanged), logs, traces, inputs and
reused ELFs. All five returned audit files match byte for byte. The audit
requires the DESIGN snapshot registered in the sealed plan
(`a4e09739...`, commit `ea7ab441`), so it read a local view substituting only
that file, as the LS6 collector did with a read-only bind. Result: 1,122 of
1,122 records complete, no errors, no missing or duplicate cases; case slots
3,022 pass, 470 fail, 3,138 skip, 0 missing. Failures remain unattributed.

Replay roster frozen from that verified audit by the unchanged
`prepare_replay_plan.py`: 274 full-application launches covering all 470
observed case failures; f4-rtc 27, f4-counter 44, f4-seconds 35, f767-rtc 27,
f767-counter 44, f767-seconds 35, f746-rtc 27, f746-seconds 35. H753 has no
failures and no replays. `replay_proposal.json` SHA-256
`c8dc42ae2e5e5b54903fba91eef03a60ba982b8f9fd0b5103182bd4e9877f84e`; it
identifies the source archive and return verification. The roster equals the
earlier records-only draft in every launch, record hash, trace hash, failed
case, unit, frequency and condition, so that condition holds with no
differences to report.

Infrastructure defect fixed before any job used it. `run_packed.sh` (SHA-256
`f7b6b6adad43724523834c5dcb7bedad2653a9a6475fb7ca751273b98f373f29`) stopped writers by process group, but task-level `timeout` moves itself
and the container to a separate group. A login-node test with the same nesting
left `timeout` and its child alive after a group TERM and nothing alive after a
session TERM. A surviving simulation would make `publish.py` refuse the archive
on a walltime interrupt. It now signals the session (SHA-256
`2507fe4593bf49785953bbe8ecb24a744b0815868117eca2dcd4e5daa8a9872b`). No scientific job has used either
version. Simulation code and the roster are unaffected.

Storage check, not an experiment: development queue, one node, 00:30:00,
TRA25006, at most 0.5 SU. It runs no firmware, no builds and never calls the
simulation body. `fixture.sbatch` (`3dda14bbfbb6cfd21c169515bd60a972d518aef12236f8d7f5e02372d334c952`),
`fixture_task.sh` (`fd51ae2dd7c22d44dd3b252cc532ba53d97a16a346dce1f8a3df2968426aec15`),
`fixture_probe.py` (`44c63fe29145c200aeecc1cf465c3c7b74a54500d68325fcc2789ed6d5cc3542`) and
`fixture_check.py` (`26284bea2c6e48b1adc48887dde056d1e38ec4b51efc5709b2c5400b4c1796bb`). Thirty-two
Launcher tasks use the replay mounts and time/timeout nesting, repeat the replay
worker's read-only preconditions across the whole roster, confirm read-only
originals, SCRATCH output and private node-local runtime, then write until a real
Slurm USR1 interrupts them. It passes only if no writer survives, the interrupted
archive publishes and verifies on WORK, the output stays unchanged afterwards,
and protected checks and the primary bundle are unchanged. If it fails, replays
are not submitted and the failure is reported.

The user pre-approved the replay job on 2026-10-31 (normal queue, one node, at
most one hour, about 1 SU, TRA25006), to be submitted once the archive verifies.
Its sealed code manifest is registered in a further dated note before execution.
Replay mismatches are reported separately and never replace a primary verdict;
missing replay verdicts stay missing.

Storage check rerun note, 2026-11-01. Check job 3546137 failed after 3 seconds,
before any writer, archive or protected check, with no firmware run. This was
`runtime.sh`'s first compute-node use. `module load tacc-apptainer/1.4.1` sets
`APPTAINER_CACHEDIR` to a shared SCRATCH path, overwriting the node-local value,
and the runtime guard correctly refused to continue. `runtime.sh` (SHA-256
`94824b806985ec216e3c0b41968ce876a3588eaf73a6fb526d54279b2a933202`) now sets that variable after the module load (SHA-256 `f8c6ade9e552b51ef62da163dec0f6c33ceb8feefd838894e89c8c1ac1bc9adf`). The
other storage variables are not changed by the modules, checked on a login node.
The same storage check is rerun unchanged: development, one node, 00:30:00,
TRA25006.

Replay registration, 2026-11-01, before execution. Storage check job 3546138
COMPLETED and passed all 20 checks (receipt `storage_check_3546138.json`): a real
Slurm USR1 interrupted 32 Launcher writers, none survived, the interrupted archive
(`b26c471f...`) published and verified on WORK, loose output stayed unchanged
afterwards, the replay preconditions held for the whole roster, the primary bundle
gained nothing, and all 30,067 protected files were unchanged before and after.

Replay job: normal queue, TRA25006, one node, 01:00:00 with a ten-minute packing
reserve, 32 local Launcher workers, at most 1 SU, no rebuilds and no dependency.
Roster `replay_proposal.json` (`c8dc42ae2e5e5b54903fba91eef03a60ba982b8f9fd0b5103182bd4e9877f84e`): 274 launches, 470
case failures. Code manifest `seal/code.sha256.json` (`9d61ee5563fb13d8c80c9e2d3ae7a57e880b243cfd68040752debbce77b11b3d`),
packet `seal/submission_proposal.json` (`de4941ed3b759416b6e71ec525807dcb7a6f8864ae8209e6f4045c8a959e27a2`).
Frozen simulation body `harness/tacc_s2/worker.py` is unchanged
(`a1737e8a973b8147f6834a443e544e736723e6045dd0e0c264bddb4e7b116f86`). The packet's
`execution_authorized: false` is its generator's fixed text; authorization is the
user's pre-approval in `approval_receipt.json`. Each launch runs once. Mismatches
and missing replay verdicts are reported separately, not rerun and never substituted
for a primary verdict.

## 2026-11-02 S2 replay results and source-supported attribution, no new experiment

Replay job 3546149 completed with exit 0:0 after 00:12:26. The checked WORK
archive SHA-256 is 9247f19e878b94370e8d9ed85717dfacc787184654ab90f68d661ff1bb56dfb2.
Independent local verification confirms its 2,214 entries, extracted-stream
hashes, complete-state receipt and all 30,067 protected hashes before/after.
The unchanged comparison helper reports 274/274 identical full-application
replays covering 470/470 original assertion failures, including UART and trace
hash agreement. No original record or missing verdict was replaced. No new
job, build, simulation, reference run or manuscript edit is registered here.

Post-result attribution tables use the user-requested categories: (a) a
single-boundary waiting candidate; (b) phase-dependent failures, separating
calendar-write phase from the counter's free-running relative-alarm phase;
(c) shared-state cleanup cascades, not independent waiting defects; (d)
unresolved clock-accuracy contract. Case counts a/b/c/d are F4 1/3/1/1,
F767 1/3/1/1, F746 1/2/0/1 and H753 0/0/0/0. These categories are supported by
source, saved traces and replays but are not completed reference-based brittle
test classifications. Phase is inferred, not directly observed. The four
sealed platform include chains were checked against packaged input hashes;
each instantiates Timers.STM32F4_RTC.

Reconciliation compares all 102 same-frequency F4 settings per RTC case with
the existing isolated-case records. Pending agrees at every setting; callback
and counting have four and five isolated-fail/full-pass differences,
respectively, with none in the reverse direction. Context and preserved model
phase explain the direction but have not been experimentally isolated. No
counter/seconds isolated baseline exists. H753's short-relative capability
predicate produces ten passing seed settings and ninety skipped seed settings,
plus two skipped endpoints; its exact false-return branch is not observed.

The report, original-versus-full reconciliation and evidence ledgers are in
notes/s2_attribution_2026-10-31/s2_report_20261102_v3/. S2 reference runs need
separate source/roster registration and approval; no additional normal-queue
job or replay retry is authorized by this analysis. E, E2 and paper edits
remain held. Progress Report 2 may use these verified observed results while
clearly identifying the remaining reference/semantic limitations.

## 2026-11-02 S2 task-specific reference validation, before any reference build/run

The user authorized complete S2 reference checks before E resumption. Freeze
new reference sources under subjects/s2_references_20261102_v1/ and their new
outer adapters under harness/tacc_s2_references/. The source-preserving S2
build/run bodies, original upstream/generated inputs, forecasts, primary and
replay records remain unchanged. The exact checks, source-to-reference mapping,
ceilings, interpretation, storage and execution gates are registered in
notes/s2_reference_2026-11-02_v1/PROTOCOL.md and its sealed packet.

All eleven qualified board/application configurations receive five nominal
reference runs plus both legal endpoints (77 qualification launches). On
qualification success, 274 reference application launches cover all 470
failing primary case slots at their exact saved frequencies. Shared launches
have explicit per-case links; H753 has qualification but no failure-setting
reference launches. F767 is an F4 configuration replica in all derived tables.
Counter configuration remains non-stock, RTC-only, without subsecond mode.

RTC references check pending/readback and both callback IDs across the two
original alarm repetitions, the original counting date and exact target,
monotonicity and premature behavior. The 26-second ten-tick experimental ceiling
is ceil(11*32000/17000 + 5); its earliest check is 6125 ms. Counter references
preserve two requested relative ticks, account for the driver's extra tick,
check ID/data/ISR/counter progress, wait under ceil(4*32000/17000+5)=13 seconds,
and reject delivery before 1360 ms. The single-shot reference clears prior
callback state explicitly and retains the extra three-second no-repeat check;
its success does not make an original cleanup cascade an independent defect.
All event polling is every 20 ms. These ceilings use the conservative cohort
17--47-kHz envelope and an explicit five-second experimental service margin,
not a claimed physical ISR bound. Callback time is checked in the callback;
independent elapsed time uses the unperturbed SysTick clock.

The seconds reference retains the original 1200-ms one-to-two-tick rate check
first and separately checks ten-tick legal-clock progress. Do not replace its
rate assertion with eventual progress or label it brittle when that contract
remains unresolved. Every reference failure receives a firmware/simulator
investigation flag, not test brittleness; that flag alone does not identify
whether firmware, simulator, or an intended accuracy contract is wrong.
Missing or invalid reference verdicts stay missing. Qualification requires all
nominal cases to pass and all non-rate endpoint cases to pass; the retained
rate check's legal-endpoint failures are anticipated property outcomes.
Unexpected qualification outcomes stop evaluation and are reported.

Planned execution is development/TRA25006, one node, 02:00:00, at most 2 SUs,
four concurrent two-worker builds then 32 local Launcher runs. No normal job
is authorized by this registration; any required normal submission must have
its concrete SU estimate reported first and satisfy standing approval rules.
Builds and loose outputs use SCRATCH, private runtime/cache uses node /tmp,
and kept ELFs/logs/configuration/hashes plus raw results are packed and verified
before WORK publication, with a new headroom check immediately before copying.
Full protected-file checks run before and after. The existing storage
coordinator and frozen simulation body are unchanged; the new adapters use
new reference sources and truthful job/node/container/module provenance.

Keep full-application/isolated RTC results side by side: pending 26/26,
callback 22/26, counting 12/17 over the same 100 seeded F4 settings. The model
phase explanation is supported but not directly measured. Original counts and
forecasts are never replaced. E audit and its quota-interruption rerun amendment
follow reference validation; E2 and manuscript edits remain held.

## 2026-11-02 S2 references complete, before the E partial-record audit

Reference job 3547096 completed 0:0 in 39 minutes. Its checked archive
7b4ce8ae94d65ec889a5026e3846911d3fba7028329798de44247f4b67e92fb6
contains 3,137 verified entries; kept ELFs, configurations, build logs, raw
records/traces/logs and both 30,067-file protection checks pass independent
Mac verification. Eleven builds, 77 qualified launches, and all 274 evaluation
launches are complete without missing verdicts or harness errors. All 470
original failures have explicit per-case reference links.

All 277 waiting-failure slots passed references, as did the 88 clean-state
single-shot slots whose originals remain cleanup cascades, not independent
waiting defects. All 105 retained seconds-rate checks failed while separate
legal-clock progress passed. Those receive firmware/simulator investigation
flags, not test brittleness; the intended rate-accuracy contract remains
unresolved. These flags do not themselves prove an implementation bug. F767
remains an F4 configuration replica, and full-application/isolated results
remain side by side with phase supported but not directly measured. Full
results are in notes/s2_reference_2026-11-02_v1/REFERENCE_RESULTS.md and the
verified per-failure links. No primary record or prior reported count changed.

The next operation is the unchanged read-only partial E index audit, on a
development compute node, with new packed SCRATCH output and before/after
protection checks. It is not a rerun or new simulation. The original auditor
SHA-256 is 43364d36d82af2725a45fc33db5db45fc47a6d164c84bf9192670400eb47e952.
Only after its exact classification is verified will an additional dated
amendment freeze the incomplete/not-started retry indices. Complete records,
including finalized harness errors and missing verdicts, remain unchanged.
E2 and paper edits stay held.

## 2026-11-02 E quota-interruption recovery, before any resumed evaluation

The read-only partial-index audit 3547562 completed 0:0 in 27:08; its archive
f359400fd714d4b717ea9753dafddb0c6085d487580de598b2c7d7590b04e3d2
was independently verified, including all 16 entries, internal hashes and
both full 30,067-file protection checks. No integrity anomalies or incomplete
derived follow-ups were found. Of 17,375 evaluations, 7,824 are complete and
valid (7,549 pass, 246 fail, 29 finalized harness errors), one is incomplete
(index 7979, claim/partial monitor but no verdict), and 9,550 were not started.

Only the 9,551 incomplete/not-started indices may resume. Their exact list is
notes/e_resume_2026-11-02_v1/packet/retry_indices.json, SHA-256
3b2c67281af37b8092e9c6a4c896f2bac8beccacd8c3850579707cef4fdd7830;
selection.json (3e4d45cb27a21bd49d673d310607ca031c65edff0655820e7d89ad05e1ebff2d)
records each retained primary hash, interrupted-file hashes, and all excluded
and eligible indices. Quota-interrupted evaluations without a final verdict
are rerun under the user's approved recovery. This is distinct from finalized
harness-error missing verdicts: all 29 remain missing, as do any new finalized
missing outcomes. Existing complete records and their follow-ups are kept as is.

Before resumption, qualify the storage mounts on development without invoking
the E evaluator, Renode or a compiler; profile only the saved full-worker time
records. Freeze the fixture code/inputs before submission. The exact protocol
is notes/e_resume_2026-11-02_v1/PROTOCOL.md. Retain the original STOP, source,
execution/task seals, forecasts, ELFs and old records read only. New SCRATCH
output is overlaid at the original logical paths, with original builds and
metadata nested read only; node-local home/cache/tmp and verified archive-only
WORK publication replace the former loose-WORK runtime. No scientific code,
source, stimulus, timeout, transformation or build changes are registered.

Only after this infrastructure qualification passes may exact disjoint chunks
be frozen and submitted under the prior E recovery approval, normal/TRA25006,
one node each, at most three hours, with reported SU estimates and fresh
headroom below 700,000. Every submission has a new output namespace and actual
provenance, with no automatic retries or requeue. Job list and timing-based
chunk estimates are recorded before execution in a later seal. STOP at Phase 3
with the before/after number table; E2 and manuscript edits remain held.

## 2026-11-02 E recovery mount qualification passed; normal chunks frozen before execution

Development storage qualification 3547838 completed 0:0 in 7:05. Archive
0b7ed7e5553752c82959761167c99a826e06817122d79f0085fa8f20d41ad757
was independently checked for exact coverage (119 entries), extracted bytes,
metadata seals and both 30,067-file protected checks. All 32 actual container
mount probes passed. The 35,708 retained original E evidence files matched
the audit ledger. No firmware, Renode evaluator or compiler ran in qualification.
WORK had 687,233 files at publication, below the 700,000 E recovery gate.

All 7,824 complete primary evaluations have saved full-worker resource files,
including their automatic replay/reference work when applicable. Their elapsed
median/p95/maximum are 34.845/110.1/320.79 seconds; maximum recorded peak RSS
is 331,924 KiB. Exact profiles and family/variant/operator summaries are in the
verified qualification archive. These are infrastructure cost measurements,
not changes to scientific results.

Freeze notes/e_resume_2026-11-02_v1/packet/resume_plan.json, SHA-256
faaed0c9b07bb664fe90295a918141140ac864037b4838c1a64f376976e20b8b.
Its seven disjoint ordered chunks have 1436, 1437, 1392, 1435, 1436, 1437 and
978 indices, exactly the 9,551 previously audited eligible indices. None of
the 7,824 complete originals, including 29 harness errors, is selected. Each
job uses normal/TRA25006, one node, 32 Launcher workers, at most 03:00:00,
no automatic requeue and a ten-minute packing signal. SU reservation ceiling
is 3 per job, 21 total. The per-index budgeting rule is ceil(1.5 times the
larger of global and family/variant/operator full-worker p95 plus 10 seconds).
Each chunk has at most 8,000 budgeted seconds per worker, plus 1,800 seconds
for setup/verification/publication and one maximum-budget task tail. Estimated
node times including that reserve/tail are 2.86, 2.86, 2.81, 2.86, 2.86, 2.86
and 2.15 hours. These are budget estimates, not runtime guarantees.

The new recovery adapters only check eligible indices, preserve read-only
mounts and provide fresh SCRATCH/runtime/provenance. They exec the original
sealed worker_e.py without importing or changing its simulation loops. Original
sources, variants, ELFs, control results, forecasts, stimuli and all old code
hashes stay unchanged. The production bind arguments equal the verified fixture.
All original E evidence is rehashed before and after every chunk. A new STOP
or process/seal error fails the job; later chunks depend on successful earlier
jobs. Every job has a separate physical namespace and verified WORK archive.
Completed new missing outcomes remain missing. An interrupted job is audited
before any new selection; no blind resubmission or primary-result replacement.
The user's scoped E-recovery approval authorizes these <=3h chunks after the
specified gates; report IDs and SUs at submission, honor queue limits, and stop
on uncertain acceptance or authentication trouble. E2 and manuscript edits
remain held. STOP at Phase 3 with the before/after number table.

## 2026-11-03 E recovery complete; read-only original-evidence collection before final analysis

All seven sealed recovery jobs 3547925–3547931 completed 0:0. Independent
Mac archive/record verification covers all 9,551 resumed indices, with 9,339
passes, 212 explicit failures, zero new finalized missing outcomes, and exact
persisted-field/raw-trace replay agreement for all 212 failures. The 26 legal
failure slots have passing references (14 unique reference records). All jobs
checked 30,067 protected files and 35,708 retained old evidence files before and
after. Original 7,824 complete records, including 29 finalized harness errors,
remain unchanged; the total 17,375 is operational accounting, not the final
per-variant repair table. No source, forecast, ELF or prior record is replaced.

Before final analysis, collect existing original E evidence on one development
node under TRA25006, maximum 02:00:00 (2-SU reservation ceiling). This is a
read-only infrastructure operation, not a new experiment: no builds, Renode,
stimulus changes or pruning. The prepared collector copies every old verified
file, sealed plan/input/build/gate evidence and all existing score/replay/legal
reference files into a new SCRATCH namespace. It checks input hashes, copied
bytes and original hashes again, with full protected audits before/after.
Only an exactly verified archive and sidecars are published to WORK after fresh
headroom checks; no final evidence is retained only on SCRATCH. Code hashes:
notes/final_submission_2026-11-02_v1/original_e_collection_code_sha256.json.
An exclusive submission namespace and receipt prevent duplicate attempts.

The human explicitly waived the former Phase 3 human-approval stop on
2026-11-02. The complete evidence package and before/after number ledger must
still be internally verified before manuscript edits; then authorized Phases
C and D proceed automatically. E2 remains held, failed references remain
firmware/simulator/contract investigations, F767 remains an F4 configuration
replica, and supported phase carryover is not described as directly measured.

## 2026-11-03 Final offline reconciliation and submission artifact

Collector 3549010 completed on development without new simulation/build/prune.
Its returned inventory and all original hashes were independently verified.
The union of original and recovered primary indices is complete: 17,375 records,
16,888 pass, 458 fail, and 29 retained finalized harness errors. All 458 failures
match their saved replay fields and raw traces; all 112 legal-failure reference
links pass. The core RTC cohort's 12 original missing outcomes remain missing;
repair V0 diagnostics do not replace them. The full before/after ledger,
per-variant/subject results, S2 references, examples and sensitivity/two-axis
analyses are in the final submission Phase 3 package. This is offline analysis
of existing evidence, not a new experiment or a change to frozen measurements.

The internally reviewed evidence checkpoint passed before the authorized paper
revision. Every manuscript table is generated by the offline reconciliation;
`make tables` verifies and restores a separately hashed publication archive,
recounts raw records, checks replays/references and compares all eight table
hashes. DATA.md and the machine file/field catalogue document units, row meanings,
missingness, provenance and TACC commands. The final local protected audit checks
all 30,067 original protected files unchanged. A fresh GitHub clone with the
cached release archive rebuilt all eight tables exactly without Renode. The
release must not claim network retrieval until upload/download is verified.
E2 and new scientific experiments remain held. Failed S2 rate references remain
firmware/simulator/accuracy-contract investigations, F767 remains an F4
configuration replica and the phase explanation remains supported, not measured.

## 2026-11-04 Separate fixed-setting F4 repeatability study (pre-execution)

The user authorized exactly30 fresh-process repeats in each of six cells:
rtc_api.test_alarm_callback at23673,23847,32000Hz and
counter_basic.test_all_channels at29143,29352,32000Hz. Run unchanged archived
F4 full-application ELFs and unchanged S2 simulation instructions; no rebuild,
source instrumentation, isolation, clock resampling, new driver or fault. The
nominal32000Hz cells are verified against archived qualification, not the seeded
production schedule. Both qualification and production use exactly the same
ELFs. Boundary and nominal records, linked logs, input hashes and resource
measurements were checked before sealing.

Protocol: notes/fixed_repeatability_2026-11-04_v1/PROTOCOL.md, SHA256
8871169a60dbb37b3be2aa52d668b5a5ba609a35aca8c16b5ca5b7c63ccd7da2.
COST.json freezes two independent development/TRA25006 jobs, one node and32
Launcher workers each,90 launches per job: RTC01:30:00 ceiling1.5SU; counter
02:00:00 ceiling2SU. Estimated total2.441906SU, reservation ceiling3.5SU, excluding
queue wait. Uses tacc-apptainer/1.4.1, launcher/3.10 and the existing calibrated
SIF. Original CPU16MIPS, SysTick16MHz, quantum1000ns, observation step0.5virtual
seconds, per-app timeouts, full application order and ELF bytes remain fixed.

Keep all180 planned indices; report pass/fail/skip/missing separately per cell.
Only complete error-free unambiguous application records supply primary selected
verdicts. Missing/harness outcomes are retained, never replaced. Mixed explicit
pass/fail within a cell supports observed same-setting flakiness in that cell;
concordance means no observed same-setting flakiness, not exclusion of rare
flakiness. No outcome-dependent repeats or stopping. Timelines distinguish UART
kernel-reported duration, sampled simulator observation and source inference;
callback-entry and subsecond-phase timestamps are not directly measured.

New namespace only, SCRATCH/node-local runtime and per-job verified packed WORK
archives with fresh headroom gates and before/after protected audits. Archived
ELFs and active counter-repair inputs stay read only; no git clean, pruning,
resubmission or alteration of3552460-3552463. No fourth-case manuscript result
before that chain is collected and verified. An exact user-supplied follow-up
prompt is retained for delivery after all four existing jobs finish. No normal
queue repeatability job is covered by this development-only plan.

## 2026-11-04 Approved path-only fixed-setting repeatability recovery (pre-execution)

The user approved recovery and a combined4.0-SU ceiling. Jobs3552681/3552682
failed at the actual SIF hash guard before any Launcher/Renode process or
primary index. Both failed archives were independently verified with6entries,
zero primary records and30,067 unchanged protected files. Retain them unchanged.
All180selected indices are not started; no observed or finalized missing verdict
is replaced. This is not a completed-study rerun.

The original6cells/30repeats, archived ELFs, test sources, frequencies, simulation
body, CPU/SysTick, quantum, observation step, timeouts and analysis rules stay
unchanged. Reuse the original sealed plan9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613.
Correct only the selected physical image from v9 to the existing calibrated v10
path tacc_work/20261023-v10/images/rtc-ls6-v1.sif, preserving the already sealed
94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
hash. Keep full compute-node image hashing. New submission helper and v2
receipt/log paths are under notes/fixed_repeatability_recovery_2026-11-04_v1.
Its approved protocol SHA256 is 06239964822bd2ccc75dd818da84b571da3ec2221d533feea939f20f1fa35466.

Fresh development/TRA25006 jobs keep one node32workers, RTC1.5h and counter2h,
3.5SU fresh reservation ceiling and2.441906SU fresh estimate. Estimated prior
minimum charges0.5SU yield2.941906SU combined estimate and4.0SU approved
combined ceiling; prior charges remain estimated pending accounting. All runtime
and output packing safeguards remain. No counter-repair3552460-3552463 input,
source, job or record is changed, resubmitted or canceled. No paper edit.
A new mismatch is preserved and reported; no blind repeat or missing replacement.


## 2026-11-05 Counter-repair infrastructure diagnosis before recovery

The separate fixed-setting repeatability study completed with 180 independently
verified selected verdicts, no selected skips/missing outcomes, and no observed
same-setting flakiness in its six cells. Its original archived inputs, 30,067
protected files, and all 20 counter-repair sealed files are unchanged.

Counter build 3552460 completed on c304-021. Gate 3552461 failed 127:0 after
two seconds on c314-191: Lmod init/executable paths were unavailable and
`apptainer` was not found. Original jobs 3552462/3552463 remain pending; no
counter-repair scientific outcome is inferred from these Slurm states.

Before any engineering recovery, register one read-only development/TRA25006
compute audit, one node, 15-minute limit and 0.25-SU reservation ceiling.
Protocol: notes/counter_repair_recovery_2026-11-05_v1/PROTOCOL.md. It verifies
pinned modules and the calibrated SIF with /bin/true only, all original
counter-plan/source/code hashes, saved build records/ELFs/logs/config products,
existing primary indices, and before/after protected hashes. It does not run
Renode, build, alter an input, cancel or resubmit an original job, or edit the
manuscript. Loose diagnostic output uses SCRATCH/tmp and is archived and
verified before publication to WORK; originals are retained without pruning.

A compute-node module mount problem is a hypothesis, not yet a root-cause
finding. The audit must verify the old gate's actual absence/presence of
primary outcomes rather than assume no starts. Unexpected records or hash
mismatches stop recovery planning. Retain failed evidence. A recovery needs a
new engineering plan/output namespace, unchanged scientific worker/settings,
and explicit approval of the new normal-job work, node count, wall limits and
SU estimates. This note authorizes no replacement normal submission.


### 2026-11-05 Diagnostic packaging correction before its first submission

The read-only pre-pull check encountered a Mac-only HANDOFF.md absent on LS6;
no diagnostic was submitted, no observed digest changed, and no original file
was repaired or replaced. The 20-file Mac source/document seal is distinct
from the 764-file active LS6 execution/input seal frozen in the repeatability
packet. The new infrastructure audit now checks the full active remote seal
on compute, keeps the Mac-only seal checked locally, and carries a byte-identical
scientific protocol copy in its new namespace. Its registered archive includes
active runtime input files and saved kept build artifacts, without deleting any
original. This correction precedes all diagnostic execution and changes no
scientific worker, source, ELF, schedule, outcome, or original job.
