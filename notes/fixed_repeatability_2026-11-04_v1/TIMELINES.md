# Evidence-linked timing timelines (archived baseline, no new run)

These timelines deliberately distinguish three clocks/claims: kernel-reported case duration in UART; Renode virtual time when buffered UART verdicts become visible to the harness; and source-derived ideal RTC timing. They are not interchangeable. No callback-entry or subsecond-phase timestamp was measured. The new repeatability study leaves the ELFs and instrumentation unchanged.

## rtc_api.test_alarm_callback

Source: [subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c).

**Source inference:** each callback iteration sleeps3s, checks no premature callback, sleeps10s, then requires callback status (lines120-141). The loop has two iterations and resets RTC calendar time (lines113-147). A complete26s test duration is compatible with reaching the second window; the UART does not directly log the loop index or callback timestamp.

**Clock arithmetic, not measured event time:** at input f, one RTC tick ideally takes32000/f virtual seconds. An alarm ten calendar ticks ahead can need nine to ten ticks depending on preserved subsecond phase. Thus the13s wait is phase-sensitive. The relevant phase is not recorded; pass/fail boundaries alone cannot measure it.

**Measured evidence limit:** the trace records UART exposure only at sampling points. A completion observed at52.5s or53s is the harness seeing buffered output, not proof that the callback/assertion occurred then. UART durations are separately labeled kernel-reported, not converted to Renode timestamps.

| Input Hz | Archived verdict | UART case duration (kernel-reported s) | First trace observation containing verdict (Renode virtual s) | Evidence |
|---:|---|---:|---:|---|
|23673|fail|26.002|52.5|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/uart/f4-rtc-seeded-990.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/traces/f4-rtc-seeded-990.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/records/f4-rtc-seeded-990.json)|
|23847|pass|26.001|53|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/uart/f4-rtc-seeded-165.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/traces/f4-rtc-seeded-165.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/records/f4-rtc-seeded-165.json)|
|32000|pass|26.001|62.5|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/uart/f4-rtc-nominal-000.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/traces/f4-rtc-nominal-000.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/records/f4-rtc-nominal-000.json)|

The32000Hz row displays the first of five archived nominal runs, not a new repeatability outcome. All five input hashes and outcomes are in input_verification.json.

## counter_basic.test_all_channels

Source: [subjects/upstream/zephyr/tests/drivers/counter/counter_basic_api/src/test_counter.c](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/subjects/upstream/zephyr/tests/drivers/counter/counter_basic_api/src/test_counter.c).

**Source inference:** the test requests a two-tick relative alarm and busy-waits1.5 times counter_ticks_to_us(ticks), then asserts cnt==nchan (lines661-701; failure site695). On the nominal1Hz RTC counter, the source wait expression is3000000us. Successful cleanup follows the assertion; a failure skips that cleanup.

**Source inference:** counter_ll_stm32_rtc.c adds one compensating tick for a partially started tick. The physical interval can therefore span two to three RTC ticks. The fixed3s wait yields a phase envelope21.333-32.000kHz; this is a source-derived envelope, not a directly measured phase or universal threshold.

**Measured ordering:** at29143Hz the archived UART reports all_channels FAIL, then later single_shot_alarm_notop FAIL with err:-16. At29352Hz both explicitly PASS in the same application. This supports the cleanup-cascade explanation; no callback-entry timestamp was recorded. A long final application observation time does not locate the selected callback.

| Input Hz | Archived verdict | UART case duration (kernel-reported s) | First trace observation containing verdict (Renode virtual s) | Evidence |
|---:|---|---:|---:|---|
|29143|fail|3.002|6|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/uart/f4-counter-seeded-1057.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/traces/f4-counter-seeded-1057.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/records/f4-counter-seeded-1057.json)|
|29352|pass|3.101|323|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/uart/f4-counter-seeded-276.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/traces/f4-counter-seeded-276.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/records/f4-counter-seeded-276.json)|
|32000|pass|3.101|323|[UART](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/uart/f4-counter-nominal-012.log), [trace](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/traces/f4-counter-nominal-012.json), [record](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/records/f4-counter-nominal-012.json)|

The32000Hz row displays the first of five archived nominal runs, not a new repeatability outcome. All five input hashes and outcomes are in input_verification.json.

