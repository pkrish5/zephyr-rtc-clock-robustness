# Final S2 qualification cohort, 2026-10-26

All15 continuation settings passed the prospective acceptance rule. The two
F767 counter_seconds assertion failures were anticipated clock-rate outcomes,
not harness errors. `cohort.csv` gives all11 retained board/application
configurations, declared/runnable/capability-skipped case counts and expected
production launches. `per_case_cohort.csv` lists every retained case.
`report.json` records the source attempt/hash for each observation.

Per board, nominal runnable/capability-skipped counts are F4 10/9, F767 10/9,
F746 6/2 and H753 9/10. These are board-specific baselines, not independent
pooled subjects or fixed per-frequency production outcomes. Every declared
case remains compiled and evaluated at each production setting. The non-stock
RTC-only/no-subsecond counter configuration remains disclosed.

Production:100 saved legal settings plus both endpoints per configuration,
1122 full-application launches and6630 case-verdict slots including skips.
Original missing outcomes stay missing in their original attempt namespace.
F746 counter is excluded for an MPU fault, allF072 for no test output (no
confirmed runtime-divider finding), and watchdog for no demonstrated reboot.
F746 RTC and counter_seconds completed all gates and are retained.

Primary estimated cost updates from provisional4.48SU to4.541397265625SU
(4.54 rounded), using the same32-worker/1.5-margin formula and returned
per-application maximum wall times. Source:report.json configurations;
F4 counter max1273.603s and F767 counter max1234.860s in the new acceptance
records. This is a new runtime estimate, not a changed test count. It excludes
replays/reference work and differs from the six-hour/6-SU reservation ceiling.

Reproduce with harness/tacc_s2_followup/finalize.py and the two extracted
qualification evidence archives. Classification of new clock failures awaits
production replay/reference attribution. No manuscript or E2 changes.
