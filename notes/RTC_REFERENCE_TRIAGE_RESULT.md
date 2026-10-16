# Reduced RTC reference-oracle triage — 2026-10-06 UTC

Status: **complete**. Registered challenges: 75 (69 failed-seed union plus six endpoints), with three separate nominal controls. Observed records: 78. Missing: 0.

The three references use the same frozen task specifications, an observable wait, a 26-second experimental ceiling, and an early-firing check. Their source and ELF hashes are in the [access-retry manifest](../results/rtc_reference_triage_access/manifest.json). The first nominal attempts in the earlier namespace crashed at virtual zero because the sandbox denied Renode history writes; those raw records remain intact. The access-retry series uses the same ELFs.

Reference outcomes: {'pass': 78}. Classification before: {'brittle_test_assumption': 112}; after: {'brittle_test_assumption': 112}.

The 75 registered challenges consumed 3051.7 summed process wall seconds (50.9 serial machine-minutes). With three task-disjoint workers, the first-to-last completion span was 1076.1 seconds (about 17.9 minutes); initial startup adds a small amount. This is an observed runtime, not a simulation-time bound.

| Task | Retained brittle assumption | Unknown after reference |
| --- | ---: | ---: |
| rtc_alarm_callback | 27 | 0 |
| rtc_alarm_pending | 67 | 0 |
| rtc_time_counting | 18 | 0 |

A passing reference supports the specific clock-threshold attribution only alongside the frozen assertion and identical original replay. A reference failure or missing result changes the corresponding flip to unknown. This is simulation triangulation, not physical-hardware proof. No original verdict, trace, or earlier classification ledger was rewritten; the [row-level before/after ledger](../analysis/rtc_reference_triage_classification.json) retains every case.
