# RTC repeatability timeline, verified recovery job 3552869

Source: [test_alarm_callback.c](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c:114). SHA256 `be76132f5b520edadedd507a9129afc1ae6c9ff06ee86d3e33ae7b69bd89c792`.

## Source-based sequence (inference, not event timestamps)

For each of two iterations, the source clears callback status, sleeps 3 seconds, checks that no callback has arrived, sleeps another 10 seconds, then requires callback status (lines 114–141). It resets the RTC calendar at lines 144–146. The 13-second waiting window is fixed in the unchanged ELF. Neither the callback entry nor the retained subsecond phase is instrumented.

## Measurements in the fresh processes

Every one of the 30 processes per cell had the same selected verdict and the same two distinct timing observations below. Kernel-reported case durations come from UART. Renode times denote when the harness first sampled output containing the verdict, not when the callback or assertion occurred. The sample interval is 0.5 virtual seconds.

|Fixed Hz|All 30 verdicts|Kernel-reported duration, s|First sampled verdict exposure, virtual s|Representative raw evidence|
|---:|---|---:|---:|---|
|23673|fail|26.002|52.5|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-000.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-000.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-000.json)|
|23847|pass|26.001|53.0|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-001.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-001.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-001.json)|
|32000|pass|26.001|62.5|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-002.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-002.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-002.json)|

All per-process record, UART and trace hashes are retained in [per_run.csv](per_run.csv). Full-application case vectors, including capability skips, are retained in [all_case_verdicts.csv](all_case_verdicts.csv). Cross-frequency pass/fail changes establish timing sensitivity; the repeated verdicts show no observed same-setting flakiness in these cells. They do not exclude rare flakiness.

The source-based phase explanation remains supported by source and cross-frequency behavior, not directly measured by these repeats. A sampled UART exposure time must not be substituted for an alarm event time or callback delivery time.
