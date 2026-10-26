# S2 continuation and submissions, 2026-10-26

## Recovery and integrity

The approved one-time checkout recovery preserved all28 collision files under
WORK/zephyr-rtc-clock-robustness/tacc_work/20261026-git-checkout-recovery-v1.
Both checkouts matched abff0ced at the recovery checkpoint, all28 restored
files matched their backups, and LS6 Git status was clean. Subsequent approved
amendment/log commits were pulled normally. The backup is retained.
All30,067 protected files still match their baseline after submission; source
and DESIGN seals also match. No original scientific record was modified.

## Calibration

3535399: development /TRA25006, one node, completed0:0 in21:44.
All15 settings meet their registered acceptance vectors, with no harness error
or unexpected verdict. Two anticipated F767 counter_seconds lower-bound
failures remain explicit failures. All347 evidence files verify independently.
Archive: results/s2_qualification_continuation_20261026_v1.
No new build; existing ELF hashes are retained.

## Final production cohort

R/S denotes five-run nominal runnable cases / explicit capability-skipped
cases. Every declared case remains compiled in production; per-setting skips
are recorded independently. Board replicas are not independent subjects.

| Board | Application | Declared | R/S | Expected launches |
|---|---|---:|---:|---:|
| STM32F4 Discovery | RTC API | 7 | 5/2 | 102 |
| STM32F4 Discovery | RTC-only counter basic | 11 | 4/7 | 102 |
| STM32F4 Discovery | Counter seconds | 1 | 1/0 | 102 |
| Nucleo-F767ZI | RTC API | 7 | 5/2 | 102 |
| Nucleo-F767ZI | RTC-only counter basic | 11 | 4/7 | 102 |
| Nucleo-F767ZI | Counter seconds | 1 | 1/0 | 102 |
| STM32F746G Discovery | RTC API | 7 | 5/2 | 102 |
| STM32F746G Discovery | Counter seconds | 1 | 1/0 | 102 |
| Nucleo-H753ZI | RTC API | 7 | 5/2 | 102 |
| Nucleo-H753ZI | RTC-only counter basic | 11 | 3/8 | 102 |
| Nucleo-H753ZI | Counter seconds | 1 | 1/0 | 102 |

Per board: F4 10/9, F767 10/9, F746 6/2, H753 9/10 runnable/skipped.
Total11 configurations,1122 full-application launches and6630 declared-case
verdict slots, including skips. All configurations have five complete nominal
and seven complete calibration applications. Counter selection is non-stock,
RTC-only, no subsecond mode. F746 counter remains excluded for the MPU fault,
F072 entirely for no test output (no confirmed divider finding), watchdog for
no demonstrated reboot. See DESIGN.md for the frozen evidence/exclusion log.

## Submitted jobs and costs

| Job | Work | Queue | Nodes | Limit | Estimated SUs | Reservation ceiling |
|---|---|---|---:|---|---:|---:|
| 3535524 | S2 primary,1122 launches | normal /TRA25006 | 1 | 6 h | 4.54 | 6 |
| 3535400 | E controls/evaluation replacement | normal /TRA25006 | 1 | 12 h | 8 | 12 |

Both were PENDING for Priority at the final scheduler check. S2 estimate uses
max measured per-application wall time,32 workers and1.5 allowance; it covers
primary runs, not later replay/reference work. The first S2 submission was
rejected with no job ID due to a redundant completed-job dependency; the
same plan was accepted after that scheduler-only argument was omitted.
Both receipts are retained, and the rejected attempt ran no firmware.

E3532543 was cancelled while pending/unstarted. Gate3532542 and the execution,
ELF and task-list hashes are unchanged; no gates or nominal runs repeated.
The new12-hour E job preserves the same registered17375 evaluations and19
controls. E2 and the manuscript remain on hold. Production results and replay/
reference attribution are not yet available; submission is not completion.

Sources: analysis/s2_qualification_final_20261026_v1/cohort.csv and report.json;
results/s2_production_20261026_v1/submission-v2.json;
notes/s2_qualification_2026-10-26_resume/e-resubmission/submission.json.
