# Verified fixed-setting timelines

The measurements below come from unchanged full-application ELFs in fresh processes. Kernel-reported case duration and sampled Renode UART exposure are distinct. Neither directly timestamps an alarm event, callback entry, or subsecond phase.

## rtc_api.test_alarm_callback

Source: [test_alarm_callback.c](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c:114), SHA256 `be76132f5b520edadedd507a9129afc1ae6c9ff06ee86d3e33ae7b69bd89c792`.

**Source-based sequence:** lines 114–141 clear callback status, sleep 3 seconds, assert no premature callback, sleep another 10 seconds, and require callback status. The constants are at lines 13–14. Lines 144–146 reset the RTC calendar, and the loop repeats twice. The unchanged ELF therefore retains the fixed 13-second window. Calendar reset does not itself measure the retained subsecond phase. The phase explanation is supported by source and cross-frequency behavior; phase and callback delivery are not directly measured.

**Measured in the repeats:** the two time values below were identical across all 30 processes per cell. UART is sampled every 0.5 Renode virtual seconds. Buffered-output exposure can occur long after the selected case; it must not be read as the callback's arrival time.

|Clock, kHz|Pass / fail / skip / missing|Kernel-reported case seconds|First sampled verdict exposure, virtual seconds|Representative evidence|
|---:|---|---:|---:|---|
|23.673|0 / 30 / 0 / 0|[26.002, 26.002]|[52.5, 52.5]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-000.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-000.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-000.json)|
|23.847|30 / 0 / 0 / 0|[26.001, 26.001]|[53.0, 53.0]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-001.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-001.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-001.json)|
|32|30 / 0 / 0 / 0|[26.001, 26.001]|[62.5, 62.5]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/records/f4-rtc-repeatability-002.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/uart/f4-rtc-repeatability-002.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552869-v1/output/traces/f4-rtc-repeatability-002.json)|

## counter_basic.test_all_channels

Source: [test_counter.c](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/tests/drivers/counter/counter_basic_api/src/test_counter.c:658), SHA256 `8f5e476627fd7386d2393c7fbc2140e67d6393308f86ba6e60c5a5cdba1ffde8`.

**Source-based sequence:** lines 669–675 compute and request a two-tick relative alarm for this pinned RTC-only configuration; line 692 busy-waits `1.5*counter_ticks_to_us(dev, ticks)` (3 seconds). Lines 693–696 check the callback count. Cleanup at lines 698–707 follows the assertion, so assertion failure bypasses it.

The [counter driver](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/drivers/counter/counter_ll_stm32_rtc.c:531) explains its compensating tick at lines 531–536. The resulting source-based two-to-three-tick interval has a 21.333–32 kHz phase envelope against a fixed 3-second wait. This is an inference from the pinned source, not a directly measured phase or universal boundary.

**Measured in the repeats:** the two time values below were identical across all 30 processes per cell. UART is sampled every 0.5 Renode virtual seconds. Buffered-output exposure can occur long after the selected case; it must not be read as the callback's arrival time.

|Clock, kHz|Pass / fail / skip / missing|Kernel-reported case seconds|First sampled verdict exposure, virtual seconds|Representative evidence|
|---:|---|---:|---:|---|
|29.143|0 / 30 / 0 / 0|[3.002, 3.002]|[6.0, 6.0]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/records/f4-counter-repeatability-090.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/uart/f4-counter-repeatability-090.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/traces/f4-counter-repeatability-090.json)|
|29.352|30 / 0 / 0 / 0|[3.101, 3.101]|[323.0, 323.0]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/records/f4-counter-repeatability-091.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/uart/f4-counter-repeatability-091.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/traces/f4-counter-repeatability-091.json)|
|32|30 / 0 / 0 / 0|[3.101, 3.101]|[323.0, 323.0]|[records](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/records/f4-counter-repeatability-092.json), [uart](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/uart/f4-counter-repeatability-092.log), [traces](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1/output/traces/f4-counter-repeatability-092.json)|

At 29.143 kHz the unchanged counter application also retains its downstream single-shot failure; the per-case vectors retain this observation. This repeatability study does not test a repair or prove that a repair removes the cascade.

All 30 selected verdicts agree within every cell: no observed same-setting flakiness in these cells under this model. Rare flakiness is not ruled out. Between-frequency differences remain timing sensitivity. No device-frequency population distribution was measured.
