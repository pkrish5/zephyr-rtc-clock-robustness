# Source-based interpretation guards for S2

Read-only preparation while calibration runs; no new experiment, raw-result
change, classification override, manuscript edit or reference implementation.
Sources are pinned Zephyr v4.3.0 and hashed in interpretation-source-hashes.json.

## Rate checking is not automatically a brittle waiting test

`tests/drivers/counter/counter_seconds/src/main.c:10-12` explicitly describes
checking that the clock ticks at roughly 1 Hz. Lines20-42 read integer counter
progress around a 1200-ms sleep and require one to two elapsed ticks.
`include/zephyr/drivers/counter.h:287-304` documents counter frequency in Hz;
`drivers/counter/counter_ll_stm32_rtc.c:840-845` computes the non-subsecond
frequency from the nominal clock and fixed prescalers. A legal oscillator
variation can violate the fixed host-time rate window, but the source's purpose
may intentionally include checking the rate. Report its clock sensitivity;
do not automatically label the failure a spurious test failure or correct
firmware violation without defining the intended clock-accuracy contract.
Reference/semantic attribution remains distinct from observing a verdict flip.

## Passing calibration API checks do not validate silicon accuracy

`tests/drivers/rtc/rtc_api/src/test_calibrate.c:17-42` checks set/get return codes
and prints the two values. It does not assert equality between the requested
and read calibration or measure the resulting timebase. Its passing case is
an API-path observation, not evidence that Renode models physical oscillator
calibration accurately. The full application still retains this case.

## Shared application state can cause a second case to fail

`tests/drivers/counter/counter_basic_api/src/test_counter.c:692-701` asserts the
all-channels callback count before alarm cancellation. `test_all_instances`
(lines225-249) performs teardown only after the test callback returns. A ztest
assertion can prevent those steps. The later single-shot test first attempts
alarm setup at lines473-476; driver lines520-522 reject an alarm while a callback
is already registered. Existing slow-clock qualification shows that later
-EBUSY failure. Preserve the observed per-case verdict, but flag the possible
cascade instead of counting an independently established deadline defect.
Do not modify the full application or run isolation diagnostics without a
separate approved protocol.

## Denominators and limitations

F746 counter is excluded for incomplete applications with an MPU fault, not
counted as capability-skipped or passed. F072 supplies no test verdicts and no
confirmed runtime-divider finding. Retain all capability-skipped cases in each
admitted application and report their per-frequency status. Board copies share
source/driver/emulator components and are not independent developer subjects.
No production failure rates or completed reference-based labels are inferred
from these source notes or the small calibration sample.
