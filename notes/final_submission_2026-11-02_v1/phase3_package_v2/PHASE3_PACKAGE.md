# Phase 3 evidence package — verify before paper edits

All registered E evaluations and S2 references have been reconciled. This package derives existing data only; it runs no Renode, changes no raw record and does not edit the manuscript. E2 remains held.

## E repair study

| Variant | Legal failures | Missing legal verdicts | Fast detected | Slow detected | Nonarrival detected | Early offset detected | Late offset detected | Median simulated s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | 106/3300 seeded; 6/66 endpoints | 9 seeded; 0 endpoints | 0/33 | 21/33 | 32/32 | 4/5 | 4/5 | 11.0 |
| V1 | 0/3300 seeded; 0/66 endpoints | 7 seeded; 0 endpoints | 0/33 | 21/33 | 33/33 | 4/5 | 4/5 | 11.0 |
| V1b | 0/3300 seeded; 0/66 endpoints | 5 seeded; 0 endpoints | 0/32 | 32/32 | 33/33 | 4/5 | 4/5 | 11.0 |
| V2 | 0/3300 seeded; 0/66 endpoints | 3 seeded; 0 endpoints | 0/33 | 33/33 | 33/33 | 4/5 | 4/5 | 11.0 |
| V3 | 0/3300 seeded; 0/66 endpoints | 2 seeded; 0 endpoints | 0/33 | 33/33 | 33/33 | 5/5 | 5/5 | 11.0 |

Duration is the median Renode virtual duration among evaluable seeded legal-clock primary runs, excluding endpoints, faults, diagnostics and harness errors; it is not callback latency. See repair_per_subject.csv for paired subject/family detail and repair_primary_index.csv for every primary index and source path. Finalized missing outcomes remain missing.

## Expanded upstream cases and reference attribution

| Board role | Runnable cases | Always skipped | Any failure | Reference-supported waits | Cascades | Firmware/simulator/contract |
| --- | --- | --- | --- | --- | --- | --- |
| F4 configuration | 10 | 9 | 6 | 4 | 1 | 1 |
| F4 configuration replica (F767) | 10 | 9 | 6 | 4 | 1 | 1 |
| F746 configuration | 6 | 2 | 4 | 3 | 0 | 1 |
| H753 configuration, narrower legal range | 10 | 9 | 0 | 0 | 0 | 0 |

All 470 original failure slots have reference outcomes. A failed seconds-rate reference is a firmware/simulator or accuracy-contract investigation, not a test defect; a passing progress check does not replace that property. F767 is an F4 configuration replica, and board replicas are not pooled as independent tests. Full per-case/skipped/missing/reference data are in s2_per_case_with_references.csv.

| Case | Isolated failures /100 | Full-app failures /100 | Isolated-fail/full-pass | Reverse differences |
| --- | --- | --- | --- | --- |
| rtc_api.test_alarm | 26 | 26 | 0 | 0 |
| rtc_api.test_alarm_callback | 26 | 22 | 4 | 0 |
| rtc_api.test_time_counting | 17 | 12 | 5 | 0 |

The phase explanation is source-supported but not directly measured. Exact source quotations and two-sentence examples are in EXAMPLES.md.

## Final statistics on the original generated cohort

Observed flip contrast: **3/34 base versus 0/32 with clock ranges**, two-sided Fisher p=0.239161. Confirmed robust yield: **55/90**; optimistic missing-outcome ceiling **63/90**, which is not a confidence interval.

| Model | Prompt | Working /15 | Confirmed robust /15 | Optimistic ceiling /15 | Robust + two detections /15 |
| --- | --- | --- | --- | --- | --- |
| luna | range_absent | 4 | 4 | 4 | 3 |
| luna | range_present | 3 | 3 | 3 | 0 |
| sol | range_absent | 15 | 10 | 13 | 8 |
| sol | range_present | 15 | 10 | 15 | 5 |
| astra | range_absent | 15 | 14 | 14 | 8 |
| astra | range_present | 14 | 14 | 14 | 14 |

All 66 eligible suites are measured; 12 original seed verdicts remain missing. E V0 reruns never replace them. The manual source-derived forecast applies to 30/66 suites; all 3,000 predictable verdicts are now measured. Most predictable vectors are zero-failure checks; the three nontrivial vectors remain separately reported. Statistics, descriptive Wilson intervals, exact paired tests and source hashes are in the accompanying ledgers.

## Distribution sensitivity

The primary normal columns condition on the documented legal interval; sigma is 5 kHz for ±3 sigma and 7.5 kHz for ±2 sigma, centered on 32 kHz. Untruncated CDFs and out-of-range mass are supplied separately. These are illustrative assumptions, not measured distributions of devices. Phase-envelope results are bounds, not fitted exact thresholds. For cascades and unresolved rate contracts, source-only shares are not identifiable; separately labeled observed monotone-step interpolation is available in sensitivity.csv and must not be presented as measured device risk.

| Case/suite | Source boundary/band, kHz | Boundary model | Uniform | Normal ±3σ, legal | Normal ±2σ, legal |
| --- | --- | --- | --- | --- | --- |
| astra-range_absent-rtc_alarm_pending-r05 | 21.333 | frozen manually source-derived scalar threshold | 14.444% | 1.514% | 5.734% |
| human-rtc_alarm_callback | 24.615 | manual source-derived ideal zero-phase threshold; counting last-poll approximation | 25.385% | 6.868% | 14.631% |
| human-rtc_alarm_pending | 24.615 | manual source-derived ideal zero-phase threshold; counting last-poll approximation | 25.385% | 6.868% | 14.631% |
| human-rtc_time_counting | 22.069 | manual source-derived ideal zero-phase threshold; counting last-poll approximation | 16.897% | 2.222% | 7.331% |
| sol-range_absent-rtc_alarm_pending-r01 | 20.000 | frozen manually source-derived scalar threshold | 10.000% | 0.687% | 3.358% |
| sol-range_absent-rtc_alarm_pending-r03 | 21.333 | frozen manually source-derived scalar threshold | 14.444% | 1.514% | 5.734% |
| f4-rtc/rtc_api.test_alarm | 24.615 | manual ideal first-case zero-phase threshold | 25.385% | 6.868% | 14.631% |
| f4-rtc/rtc_api.test_alarm_callback | 22.154–24.615 | source calendar-write phase envelope; phase not directly measured | 17.179–25.385% | 2.318–6.868% | 7.530–14.631% |
| f4-rtc/rtc_api.test_time_counting | 19.862–22.069 | source phase envelope with approximate last poll; phase not directly measured | 9.540–16.897% | 0.627–2.222% | 3.147–7.331% |
| f4-counter/counter_basic.test_single_shot_alarm_notop | not source-identified | cleanup cascade has no independent waiting boundary | not identifiable from a source-only threshold | not identifiable from a source-only threshold | not identifiable from a source-only threshold |
| f4-counter/counter_basic.test_all_channels | 21.333–32.000 | free-running relative-alarm phase envelope; distinct from calendar-write phase | 14.444–50.000% | 1.514–50.000% | 5.734–50.000% |
| f4-seconds/seconds_counter.test_seconds_rate | not source-identified | no validated source-only defect threshold; ideal zero-phase rate comparison is 32000/1.2 Hz | not identifiable from a source-only threshold | not identifiable from a source-only threshold | not identifiable from a source-only threshold |
| f767-rtc/rtc_api.test_alarm | 24.615 | manual ideal first-case zero-phase threshold | 25.385% | 6.868% | 14.631% |
| f767-rtc/rtc_api.test_alarm_callback | 22.154–24.615 | source calendar-write phase envelope; phase not directly measured | 17.179–25.385% | 2.318–6.868% | 7.530–14.631% |
| f767-rtc/rtc_api.test_time_counting | 19.862–22.069 | source phase envelope with approximate last poll; phase not directly measured | 9.540–16.897% | 0.627–2.222% | 3.147–7.331% |
| f767-counter/counter_basic.test_single_shot_alarm_notop | not source-identified | cleanup cascade has no independent waiting boundary | not identifiable from a source-only threshold | not identifiable from a source-only threshold | not identifiable from a source-only threshold |
| f767-counter/counter_basic.test_all_channels | 21.333–32.000 | free-running relative-alarm phase envelope; distinct from calendar-write phase | 14.444–50.000% | 1.514–50.000% | 5.734–50.000% |
| f767-seconds/seconds_counter.test_seconds_rate | not source-identified | no validated source-only defect threshold; ideal zero-phase rate comparison is 32000/1.2 Hz | not identifiable from a source-only threshold | not identifiable from a source-only threshold | not identifiable from a source-only threshold |
| f746-rtc/rtc_api.test_alarm | 24.615 | manual ideal first-case zero-phase threshold | 25.385% | 6.868% | 14.631% |
| f746-rtc/rtc_api.test_alarm_callback | 22.154–24.615 | source calendar-write phase envelope; phase not directly measured | 17.179–25.385% | 2.318–6.868% | 7.530–14.631% |
| f746-rtc/rtc_api.test_time_counting | 19.862–22.069 | source phase envelope with approximate last poll; phase not directly measured | 9.540–16.897% | 0.627–2.222% | 3.147–7.331% |
| f746-seconds/seconds_counter.test_seconds_rate | not source-identified | no validated source-only defect threshold; ideal zero-phase rate comparison is 32000/1.2 Hz | not identifiable from a source-only threshold | not identifiable from a source-only threshold | not identifiable from a source-only threshold |
| astra-range_absent-rtc_alarm_pending-r05--V0 | 21.333 | frozen manually source-derived scalar threshold; repeated frozen V0 context | 14.444% | 1.514% | 5.734% |
| human-rtc_alarm_callback--V0 | 24.615 | manual source-derived ideal zero-phase threshold; counting last-poll approximation; repeated frozen V0 context | 25.385% | 6.868% | 14.631% |
| human-rtc_alarm_pending--V0 | 24.615 | manual source-derived ideal zero-phase threshold; counting last-poll approximation; repeated frozen V0 context | 25.385% | 6.868% | 14.631% |
| human-rtc_time_counting--V0 | 22.069 | manual source-derived ideal zero-phase threshold; counting last-poll approximation; repeated frozen V0 context | 16.897% | 2.222% | 7.331% |
| sol-range_absent-rtc_alarm_pending-r01--V0 | 20.000 | frozen manually source-derived scalar threshold; repeated frozen V0 context | 10.000% | 0.687% | 3.358% |
| sol-range_absent-rtc_alarm_pending-r03--V0 | 21.333 | frozen manually source-derived scalar threshold; repeated frozen V0 context | 14.444% | 1.514% | 5.734% |

## Two axes: legal-clock survival and slow-fault detection

| Context | Clock status | Slow-fault status | Count |
| --- | --- | --- | --- |
| S2_full_application | not_applicable_capability_skipped | not_measured | 29 |
| S2_full_application | observed_failure | not_measured | 16 |
| S2_full_application | survives_observed_schedule | not_measured | 17 |
| S2_full_application | unconfirmed_some_settings_skipped | not_measured | 3 |
| original_generated | observed_failure | detected | 3 |
| original_generated | survives_observed_schedule | detected | 39 |
| original_generated | survives_observed_schedule | survived_fault | 16 |
| original_generated | unconfirmed_missing_verdicts | detected | 7 |
| original_generated | unconfirmed_missing_verdicts | survived_fault | 1 |
| original_isolated_upstream | observed_failure | detected | 3 |

Unknown verdicts and capability skips are not passes. Expanded full-application S2 cases have no measured slow-fault result; their unknown axis is retained in two_axis_per_subject.csv rather than inferred from isolated cases or legal-clock results.

## Before/after number ledger

See before_after_numbers.csv for every replacement/table-row change, saved pre-revision manuscript line locations and source paths, and unchanged_numbers.json for preserved original counts. Secondary paired, timing and similarity material is retained in the repository. This evidence builder never edits the manuscript. The human authorized paper revision after internal evidence review.

## Evidence checkpoint and authorized continuation

**The human removed the Phase 3 approval stop on 2026-11-02.** Internally verify this complete evidence package, then continue directly to Phase C with verified values and framing, compile within six pages including the inline bibliography, and perform the Phase D artifact/data dictionary, clean-clone reproduction and tagged-release work. Do not proceed on unresolved integrity inconsistencies. E2 remains held; the automation cannot submit normal-queue jobs.
