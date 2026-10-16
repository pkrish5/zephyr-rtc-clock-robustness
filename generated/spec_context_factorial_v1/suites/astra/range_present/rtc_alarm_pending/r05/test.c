#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define ALARM_ID 0U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define CALENDAR_BUDGET_MS 21000
#define DELIVERY_BUDGET_MS 5000
#define POLL_MS 10

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static const struct rtc_time initial_time = {
	.tm_year = 2024 - 1900, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	.tm_nsec = 0,
};

static const struct rtc_time alarm_time = {
	.tm_year = 2025 - 1900, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	.tm_nsec = 0,
};

/* Compare the full calendar, including the year rollover. */
static int calendar_compare(const struct rtc_time *a,
			    const struct rtc_time *b)
{
	const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
			   a->tm_hour, a->tm_min, a->tm_sec };
	const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
			   b->tm_hour, b->tm_min, b->tm_sec };

	for (unsigned int i = 0; i < sizeof(av) / sizeof(av[0]); ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	struct rtc_time readback = {0};
	struct rtc_time before, after;
	uint16_t supported = 0;
	uint16_t mask = 0;
	bool observed_early_clear = false;
	bool observed_pending = false;
	int64_t reached_at = -1;
	int pending;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7U, "Unexpected alarm mask");
	zassert_ok(rtc_alarm_get_supported_fields(rtc, ALARM_ID, &supported));
	zassert_equal(supported & ALARM_MASK, ALARM_MASK);

	/* Disable both board alarm channels and consume any old pending state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		pending = rtc_alarm_is_pending(rtc, id);
		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
	}

	const int64_t started_at = k_uptime_get();

	zassert_ok(rtc_set_time(rtc, &initial_time));
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm_time));
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
	zassert_equal(mask, ALARM_MASK);
	zassert_equal(readback.tm_sec, alarm_time.tm_sec);
	zassert_equal(readback.tm_min, alarm_time.tm_min);
	zassert_equal(readback.tm_hour, alarm_time.tm_hour);
	/* Date fields are intentionally excluded from the alarm mask. */

	/*
	 * At 17 kHz, one calendar second takes at most 32000/17000
	 * wall seconds. Eleven ticks (ten plus a phase allowance) take
	 * less than 21 seconds.
	 *
	 * The separate five-second delivery allowance is this test's
	 * explicit ISR/thread responsiveness requirement, NOT a bound
	 * inferred from the oscillator specification. Failure reports
	 * distinguish calendar progress from pending-state delivery.
	 * The overall observation window is 26 seconds; as with any
	 * thread-based test, a completely stalled CPU needs a harness
	 * timeout to terminate the application.
	 */
	for (;;) {
		zassert_ok(rtc_get_time(rtc, &before));
		pending = rtc_alarm_is_pending(rtc, ALARM_ID);
		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
		zassert_ok(rtc_get_time(rtc, &after));
		zassert_true(calendar_compare(&before, &after) <= 0,
			     "RTC calendar moved backwards");

		/*
		 * The second timestamp avoids falsely calling an alarm early
		 * when the RTC crosses the target during the pending query.
		 * Preserve a positive result: querying may consume it.
		 */
		if (pending == 1) {
			zassert_true(calendar_compare(&after, &alarm_time) >= 0,
				     "Alarm pending before its RTC time");
			observed_pending = true;
		}
		if (calendar_compare(&after, &alarm_time) < 0) {
			zassert_equal(pending, 0);
			observed_early_clear = true;
		}

		const int64_t now = k_uptime_get();

		if (reached_at < 0 &&
		    calendar_compare(&after, &alarm_time) >= 0) {
			reached_at = now;
		}
		if (observed_pending) {
			break;
		}
		if (reached_at < 0) {
			zassert_true(now - started_at < CALENDAR_BUDGET_MS,
				     "RTC did not reach target within 21 seconds");
		} else {
			zassert_true(now - reached_at < DELIVERY_BUDGET_MS,
				     "Pending not delivered within five seconds");
		}
		zassert_true(now - started_at <
			     CALENDAR_BUDGET_MS + DELIVERY_BUDGET_MS,
			     "Overall observation deadline expired");
		k_sleep(K_MSEC(POLL_MS));
	}

	zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL));
	zassert_true(observed_early_clear, "No pre-target clear observation");
	zassert_true(observed_pending, "No pending alarm observed");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
