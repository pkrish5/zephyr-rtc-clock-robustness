# RTC timing mutation quality checks — updated 2026-10-07 UTC

**Interpretation clarification, 2026-10-07:** The 64-kHz and 10-kHz operators alter the entire RTC calendar rate. The 0/69 fast-oscillator kills therefore show absence of an independent time-reference check in these selected tests; they do not establish that the tests would miss a firmware defect that programs the alarm compare one RTC calendar second early. A separate nominal-clock driver-offset pair is [proposed, not yet run](RTC_FIRMWARE_ALARM_OFFSET_PROPOSAL.md). Luna's three range-present eligible RTC suites are counting tests with 60-second source observation windows (3.188 times the ideal legal slow-bound ten-second transition); all survive the 32-second 10-kHz challenge. This explains that cell's 0/3 late kills as over-padding for the selected fault.

## Registered interim two-fault score

The [two-fault manifest](../results/rtc_timing_mutants_two_faults/manifest.json) ran all **66 functionally eligible AI suites** and the three matched upstream selected cases at nominal CPU/SysTick settings, once each against an intentionally illegal 64-kHz early RTC input and a 10-kHz late RTC input. The earlier 1-Hz nonarrival clock operator is invalid: it crashed the Renode RTC model before a reference verdict and is not scored. All six task-specific early/late reference activations reached their intended assertions. These are mutation challenges, **not legal timing schedules** or RQ2 seeds. The original test source and original nominal/varied ELFs remain frozen; the out-of-range clock platforms are separate saved artifacts.

With the frozen 128 × 250 RTC divider, ten calendar seconds take an ideal `320000/f_LSI` host seconds. The documented **17–47 kHz** LSI interval therefore gives an ideal calendar-arrival window of **6.809–18.824 s**. The **64-kHz early fault arrives at 5.000 s**, 1.809 s (26.6%) before the legal fastest endpoint; its input frequency is 36.2% above the documented maximum. The **10-kHz late fault arrives at 32.000 s**, 13.176 s (70.0%) after the legal slowest endpoint; its input frequency is 41.2% below the documented minimum. These calculations exclude ISR delivery, thread service, and polling phase; the faults are deliberately outside the legal-clock experiment.

The [audited row ledger](../analysis/rtc_quality_mutant_scores/rows.csv) has **138/138** suite–operator records with saved trace, UART, monitor, source, ELF, and platform hashes. There were **zero harness errors, unknowns, or timeouts**. A strict kill means an explicit failing selected ztest case; pass means survival. The two-fault outcomes remain an explicit interim historical result; the completed third fault and per-mutant intervals are reported below.

**All 69 tests survived the early fault, including upstream controls.** The early reference tests detected it because they explicitly compared RTC arrival with a legal host-time lower bound. A suite that checks only that the alarm did not fire *before the RTC calendar reaches its target* can pass even when the calendar itself runs too fast. This is a concrete oracle-strength limitation, not an assertion that a 64-kHz LSI is a legal chip behavior. The late-fault kills vary considerably by cohort and task; a suite that survives may be overpadded, omit a finite upper-bound assertion, or check a different observable. Source-level padding and wait-style evidence must be read alongside these scores.

The three matched **upstream human selected cases** each survived the early fault and explicitly failed on the late and replacement nonarrival faults:

| Upstream selected case | Early 64 kHz | Late 10 kHz | Nonarrival at nominal 32 kHz |
|---|---|---|---|
| Alarm callback | Survived | Killed | Killed |
| Alarm pending | Survived | Killed | Killed |
| Calendar counting | Survived | Killed | Killed |

Across the three upstream suites, this is **0/3 early kills** (95% Wilson 0.0–56.1%), **3/3 late kills** (43.9–100.0%), and **3/3 nonarrival kills** (43.9–100.0%). These are selected Zephyr cases, not a random sample of human tests.

The [source-only padding ledger](../analysis/rtc_padding_audit.csv) helps separate those explanations for the 66 AI suites. **All 12 suites classified over-padded (`>2×` the ideal 17-kHz legal slow bound) survived the 10-kHz late mutant. All 18 suites with an assessable budget at or below 2× killed it.** Of the 36 suites without a defensible scalar clock-only budget, 31 killed the late mutant and five survived. This is a descriptive cross-tab, not proof that every survivor is vacuous: a source may exercise a different oracle, and the 10-kHz fault is intentionally outside the legal range. The row ledgers preserve the five unknown-budget survivors for manual inspection.

## Replacement nonarrival operator — completed

The [nominal-clock driver-path replacement](../results/rtc_nonarrival_driver_v3/manifest.json) suppresses alarm callback/pending delivery after interrupt acknowledgement, or freezes the value returned by the calendar-read API in counting tests. It does not change the RTC clock input. This intentionally faulty driver variant uses separate rebuilt ELFs; it is not a legal-schedule, frozen-binary RQ2 run. The [activation audit](../results/rtc_nonarrival_driver_v3/activation_audit.json) confirms **3/3** reference failures at the registered nonarrival ceiling assertions.

All **69/69 planned suite records** are now present. Thirty-two were saved in the original namespace and 37 in an [append-only recovery registration](../results/rtc_nonarrival_driver_v3_resume/manifest.json) after an interrupted execution left three monitor/UART files without verdict records. The original partial artifacts were hashed and preserved. The [audited row ledger](../analysis/rtc_quality_mutant_scores/rows.csv) links each suite to its original or recovery result and checks manifest, source, ELF, simulator, platform, trace, UART, and monitor hashes. **68/69** nonarrival challenges produced explicit assertion failures; the sole remainder, `luna-range_absent-rtc_time_counting-r05`, is a Renode monitor startup `harness_error` at virtual zero and is **unevaluable**, not a survivor or a kill. No diagnostic verdict replaces it.

Across the three selected faults, AI suites killed **114/197 evaluable challenges** (198 planned) and upstream selected cases killed **6/9**. These pooled counts repeat each suite across faults and are not treated as independent binomial trials; the per-fault suite shares and Wilson intervals appear below.

The validated nonarrival fault is detected by every evaluable test, while **no test detects the early-clock fault**. Thus a zero legal-clock flip rate cannot by itself distinguish a strong test from an over-padded, latency-dependent, or weakly bounded oracle. These are three deliberately selected mutants, not a representative fault distribution; the score is descriptive and correlated by task. The late-fault/padding cross-tab below remains a separate explanation of why some suites survive the late fault.

## Model, prompt, wait-style, and padding cross-tabs

Each fraction counts **suite-level mutant kills / evaluable suite challenges**. Parentheses give a 95% Wilson interval for that selected cohort's kill share. The intervals are descriptive: suites share tasks and the three faults were purposively chosen, so these are not confidence intervals for all possible tests or defects. “Both” uses the same suite as the unit and requires explicit kills of both early and late faults. The one nonarrival startup harness error stays missing; it is excluded only from that fault's evaluable denominator. Full counts and interval precision are in the [derived cross-tab audit](../analysis/rtc_quality_cross_tabs.json).

### Mutant × model × prompt, including upstream controls

| Model | Prompt | Suites | Early kill [95% CI] | Late kill [95% CI] | Nonarrival kill [95% CI] | Both early + late [95% CI] |
|---|---|---:|---:|---:|---:|---:|
| Astra | Absent | 15 | 0/15 (0.0–20.4%) | 9/15 (35.7–80.2%) | 15/15 (79.6–100.0%) | 0/15 (0.0–20.4%) |
| Astra | Present | 14 | 0/14 (0.0–21.5%) | 14/14 (78.5–100.0%) | 14/14 (78.5–100.0%) | 0/14 (0.0–21.5%) |
| Human | — | 3 | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) | 3/3 (43.9–100.0%) | 0/3 (0.0–56.1%) |
| Luna | Absent | 4 | 0/4 (0.0–49.0%) | 4/4 (51.0–100.0%) | 3/3 (43.9–100.0%); 1 missing | 0/4 (0.0–49.0%) |
| Luna | Present | 3 | 0/3 (0.0–56.1%) | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) | 0/3 (0.0–56.1%) |
| Sol | Absent | 15 | 0/15 (0.0–20.4%) | 13/15 (62.1–96.3%) | 15/15 (79.6–100.0%) | 0/15 (0.0–20.4%) |
| Sol | Present | 15 | 0/15 (0.0–20.4%) | 9/15 (35.7–80.2%) | 15/15 (79.6–100.0%) | 0/15 (0.0–20.4%) |
| **All AI** | **Both** | **66** | **0/66 (0.0–5.5%)** | **49/66 (62.6–83.3%)** | **65/65 (94.4–100.0%); 1 missing** | **0/66 (0.0–5.5%)** |

**No suite in any cohort killed both early and late faults**, because no suite killed the early fault. Range context did not yield a uniform late-fault advantage: Astra present killed 14/14 versus absent 9/15; Sol present killed 9/15 versus absent 13/15; Luna present killed 0/3 versus absent 4/4. These are small, task-correlated cells, and Luna's eligible RTC set is counting-only. Every evaluable suite killed the nonarrival fault, including upstream controls. The early-fault reference detected the 64-kHz input using an external lower arrival bound that the scored suites did not assert.

### Cross-tab by source wait style

“Fixed only” has a `k_sleep`/busy-wait-family call and no event-wait API call; “event only” has an event-wait call but no fixed sleep; “fixed + event” has both. These syntactic categories do not establish adequacy. Calendar and pending polling flags can overlap them; see the [source inventory](../analysis/rtc_static_waits.csv).

| Model | Prompt | Wait style | Suites | Early kill [95% CI] | Late kill [95% CI] | Nonarrival kill [95% CI] |
|---|---|---|---:|---:|---:|---:|
| Astra | Absent | Event only | 5 | 0/5 (0.0–43.4%) | 4/5 (37.6–96.4%) | 5/5 (56.6–100.0%) |
| Astra | Absent | Fixed only | 10 | 0/10 (0.0–27.8%) | 5/10 (23.7–76.3%) | 10/10 (72.2–100.0%) |
| Astra | Present | Event only | 2 | 0/2 (0.0–65.8%) | 2/2 (34.2–100.0%) | 2/2 (34.2–100.0%) |
| Astra | Present | Fixed only | 12 | 0/12 (0.0–24.2%) | 12/12 (75.8–100.0%) | 12/12 (75.8–100.0%) |
| Human | — | Fixed only | 3 | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) | 3/3 (43.9–100.0%) |
| Luna | Absent | Fixed only | 4 | 0/4 (0.0–49.0%) | 4/4 (51.0–100.0%) | 3/3 (43.9–100.0%); 1 missing |
| Luna | Present | Fixed only | 3 | 0/3 (0.0–56.1%) | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) |
| Sol | Absent | Fixed + event | 1 | 0/1 (0.0–79.3%) | 1/1 (20.7–100.0%) | 1/1 (20.7–100.0%) |
| Sol | Absent | Fixed only | 14 | 0/14 (0.0–21.5%) | 12/14 (60.1–96.0%) | 14/14 (78.5–100.0%) |
| Sol | Present | Event only | 2 | 0/2 (0.0–65.8%) | 1/2 (9.5–90.5%) | 2/2 (34.2–100.0%) |
| Sol | Present | Fixed + event | 3 | 0/3 (0.0–56.1%) | 2/3 (20.8–93.9%) | 3/3 (43.9–100.0%) |
| Sol | Present | Fixed only | 10 | 0/10 (0.0–27.8%) | 6/10 (31.3–83.2%) | 10/10 (72.2–100.0%) |

Across AI suites, late kills were 39/53 (95% Wilson 60.4–83.6%) for fixed-only, 7/9 (45.3–93.7%) for event-only, and 3/4 (30.1–95.4%) for mixed waits. Early kills were zero in every wait category. Event waiting alone therefore did not supply the missing external early-firing bound.

### Cross-tab by legal-bound padding

“Over-padded” means an assessable source observation budget greater than twice the ideal ten-RTC-second arrival time at the legal 17-kHz slow endpoint. “≤2× bound” includes shorter as well as near-bound budgets; it does not certify end-to-end ISR service. “Unknown bound” means callback delivery, pending service, or control flow prevented a defensible scalar clock-only budget. Upstream tests were not coded in this AI padding ledger.

| Model | Prompt | Padding class | Suites | Early kill [95% CI] | Late kill [95% CI] | Nonarrival kill [95% CI] |
|---|---|---|---:|---:|---:|---:|
| Astra | Absent | ≤2× bound | 1 | 0/1 (0.0–79.3%) | 1/1 (20.7–100.0%) | 1/1 (20.7–100.0%) |
| Astra | Absent | Unknown bound | 9 | 0/9 (0.0–29.9%) | 8/9 (56.5–98.0%) | 9/9 (70.1–100.0%) |
| Astra | Absent | Over-padded | 5 | 0/5 (0.0–43.4%) | 0/5 (0.0–43.4%) | 5/5 (56.6–100.0%) |
| Astra | Present | ≤2× bound | 5 | 0/5 (0.0–43.4%) | 5/5 (56.6–100.0%) | 5/5 (56.6–100.0%) |
| Astra | Present | Unknown bound | 9 | 0/9 (0.0–29.9%) | 9/9 (70.1–100.0%) | 9/9 (70.1–100.0%) |
| Human | — | Not coded | 3 | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) | 3/3 (43.9–100.0%) |
| Luna | Absent | ≤2× bound | 4 | 0/4 (0.0–49.0%) | 4/4 (51.0–100.0%) | 3/3 (43.9–100.0%); 1 missing |
| Luna | Present | Over-padded | 3 | 0/3 (0.0–56.1%) | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) |
| Sol | Absent | ≤2× bound | 5 | 0/5 (0.0–43.4%) | 5/5 (56.6–100.0%) | 5/5 (56.6–100.0%) |
| Sol | Absent | Unknown bound | 8 | 0/8 (0.0–32.4%) | 8/8 (67.6–100.0%) | 8/8 (67.6–100.0%) |
| Sol | Absent | Over-padded | 2 | 0/2 (0.0–65.8%) | 0/2 (0.0–65.8%) | 2/2 (34.2–100.0%) |
| Sol | Present | ≤2× bound | 3 | 0/3 (0.0–56.1%) | 3/3 (43.9–100.0%) | 3/3 (43.9–100.0%) |
| Sol | Present | Unknown bound | 10 | 0/10 (0.0–27.8%) | 6/10 (31.3–83.2%) | 10/10 (72.2–100.0%) |
| Sol | Present | Over-padded | 2 | 0/2 (0.0–65.8%) | 0/2 (0.0–65.8%) | 2/2 (34.2–100.0%) |

All **12/12 over-padded AI suites survived the late fault** (0/12 late kills; 95% Wilson 0.0–24.2%); all **18/18** with an assessable ≤2× bound killed it (82.4–100.0%); **31/36** unknown-bound suites killed it (71.3–93.9%). The pattern shows that some legal-clock survivors have broad upper windows, while others have unassessed delivery or control-flow behavior. It does not show that a longer timeout is an acceptable repair. Early kills remain zero in every padding stratum.

### Latency premises among the 47 measured AI suites with zero clock-rate failures

These post-start source labels overlap the wait and padding categories. They describe unsupported delivery or ordering premises that the legal LSI-rate schedule may miss. Counts are suites, not seed runs.

| Model | Prompt | Zero-clock-failure suites | Definite latency premise | Unknown | None found |
|---|---|---:|---:|---:|---:|
| Astra | Absent | 10 | 5 | 5 | 0 |
| Astra | Present | 11 | 5 | 5 | 1 |
| Luna | Absent | 2 | 1 | 1 | 0 |
| Luna | Present | 2 | 1 | 0 | 1 |
| Sol | Absent | 9 | 6 | 3 | 0 |
| Sol | Present | 13 | 3 | 9 | 1 |
| **All models** | **Absent** | **21** | **12** | **9** | **0** |
| **All models** | **Present** | **26** | **9** | **14** | **3** |

The pooled absent/present split is **12/21 versus 9/26 definite** and **9/21 versus 14/26 unknown** among these zero-clock-failure suites. **We retract any general substitution-effect interpretation** that range context moved tests from clock assumptions toward latency assumptions: these descriptive counts do not support it, and the failed delivery-delay pilot supplies no dynamic validation. The historical bound-context supplement `r05`, with an immediate second-callback `K_NO_WAIT` check, remains an **illustrative case only** outside the factorial sample and every model/prompt denominator.

## Reproduce

From the repository root, `python3 analysis/rtc_quality_mutant_scores.py` audits registered results and regenerates the [summary](../analysis/rtc_quality_mutant_scores/summary.json) and row ledger. Then `python3 analysis/rtc_quality_cross_tabs.py` verifies the source joins and computes all Wilson intervals in the [cross-tab audit](../analysis/rtc_quality_cross_tabs.json). Original records are never overwritten. The old invalid activation remains in `results/rtc_timing_mutants/`; two superseded nonarrival engineering registrations (`results/rtc_nonarrival_driver/` and `results/rtc_nonarrival_driver_v2/`) produced no simulator verdict and do not enter any score.
