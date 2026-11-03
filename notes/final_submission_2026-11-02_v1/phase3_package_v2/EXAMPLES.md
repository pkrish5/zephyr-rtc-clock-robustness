# Exact source examples

## phase_dependent_F4_counting

**Application:** RTC API, full application. **Case:** `rtc_api.test_time_counting`.

Observed failing band: 17000–20500 Hz; passing band: 20701–47000 Hz. Source boundary/band: 19.862--22.069 kHz phase envelope; last-poll approximation.

The test rewrites the RTC calendar, then polls every 500 ms, with its last observation about 14.5 simulated seconds after the write. Renode preserves the fractional count across the write, so phase carried from earlier cases can shift the failure boundary; that explanation is supported by source and reconciliation but was not directly measured.

Source: `subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_time_incrementing.c`. Line labels below are metadata; code text is copied exactly.

Lines 15–17:

```c
#define RTC_TEST_TIME_COUNTING_SET_TIME	  (1767225595UL)
#define RTC_TEST_TIME_COUNTING_LIMIT	  (RTC_TEST_TIME_COUNTING_SET_TIME + 10UL)
#define RTC_TEST_TIME_COUNTING_POLL_LIMIT (30U)
```

Lines 35–59:

```c
	zassert_equal(rtc_set_time(rtc, &datetime_set), 0, "Failed to set time");

	for (i = 0; i < RTC_TEST_TIME_COUNTING_POLL_LIMIT; i++) {
		/* Get time */
		zassert_equal(rtc_get_time(rtc, &datetime_get), 0, "Failed to get time");

		timer_get = timeutil_timegm((struct tm *)(&datetime_get));

		/* Validate if time incrementing */
		zassert_true(timer_get_last <= timer_get, "Time is decrementing");

		/* Check if limit reached */
		if (timer_get == RTC_TEST_TIME_COUNTING_LIMIT) {
			break;
		}

		/* Save last timer get */
		timer_get_last = timer_get;

		/* Limit polling rate */
		k_msleep(500);
	}

	zassert_true(i < RTC_TEST_TIME_COUNTING_POLL_LIMIT,
		     "Timeout occurred waiting for time to increment");
```

## F4_counter_seconds_rate

**Application:** Counter seconds, RTC-only non-stock configuration. **Case:** `seconds_counter.test_seconds_rate`.

Observed failing band: 17000–26168 Hz; passing band: 27086–47000 Hz. Source boundary/band: 26.667 kHz ideal zero-phase comparison; not a validated defect boundary.

The test samples the counter around a 1,200-ms sleep and requires a change of one or two ticks. At slow legal inputs its retained rate reference also fails while eventual progress passes, so these outcomes remain a firmware/simulator or accuracy-contract investigation rather than evidence of a faulty test.

Source: `subjects/upstream/zephyr/tests/drivers/counter/counter_seconds/src/main.c`. Line labels below are metadata; code text is copied exactly.

Lines 10–12:

```c
/*
 * Basic test to ensure that the clock is ticking at roughly 1Hz.
 */
```

Lines 20–42:

```c
#define DELAY_MS 1200	/* pause 1.2 seconds should always pass */
#define MIN_BOUND 1	/* counter must report at least MIN_BOUND .. */
#define MAX_BOUND 2	/* .. but at most MAX_BOUND seconds elapsed */

ZTEST(seconds_counter, test_seconds_rate)
{
	const struct device *const dev = DEVICE_DT_GET(CTR_DEV);
	uint32_t start, elapsed;
	int err;

	zassert_true(device_is_ready(dev), "counter device is not ready");

	err = counter_get_value(dev, &start);
	zassert_true(err == 0, "failed to read counter device");

	k_msleep(DELAY_MS);

	err = counter_get_value(dev, &elapsed);
	zassert_true(err == 0, "failed to read counter device");
	elapsed -= start;

	zassert_true(elapsed >= MIN_BOUND, "busted minimum bound");
	zassert_true(elapsed <= MAX_BOUND, "busted maximum bound");
```

## original_upstream_callback

**Application:** RTC API; full-application and original isolated contexts. **Case:** `rtc_api.test_alarm_callback`.

Observed failing band: 17000–23673 Hz; passing band: 23847–47000 Hz. Source boundary/band: 22.154--24.615 kHz phase envelope; no unique source-only threshold.

The original callback test checks absence after three simulated seconds and eventual callback presence after another ten, without asserting equality to the requested calendar second. Its isolated and full-application contexts have different observed boundaries, consistent with a preserved phase explanation that has not been directly measured.

Source: `subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c`. Line labels below are metadata; code text is copied exactly.

Lines 13–14:

```c
#define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
#define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
```

Lines 119–141:

```c
		/* Wait before validating alarm callbacks have not been called prematurely */
		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY));

		/* Validate alarm callbacks have not been called prematurely */
		callback_called_mask_status_odd = atomic_get(&callback_called_mask_odd);
		callback_called_mask_status_even = atomic_get(&callback_called_mask_even);

		zassert_equal(callback_called_mask_status_odd, 0,
			      "Alarm callback called prematurely");
		zassert_equal(callback_called_mask_status_even, 0,
			      "Alarm callback called prematurely");

		/* Wait for alarm to trigger */
		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));

		/* Validate alarm callback called */
		for (uint16_t j = 0; j < alarms_count; j++) {
			callback_called_status =
				(j % 2) ? atomic_test_bit(&callback_called_mask_odd, j)
					: atomic_test_bit(&callback_called_mask_even, j);

			zassert_equal(callback_called_status, true,
				      "Alarm %d callback should have been called", j);
```

Original isolated context: 26/100 seeded failures; full application: 22/100. The 4 differences are isolated-fail/full-pass; no directly measured phase value is claimed.

