#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#include <stdint.h>
#include <time.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

static int64_t calendar_seconds(const struct rtc_time *rtc)
{
	struct tm calendar = {
		.tm_sec = rtc->tm_sec,
		.tm_min = rtc->tm_min,
		.tm_hour = rtc->tm_hour,
		.tm_mday = rtc->tm_mday,
		.tm_mon = rtc->tm_mon,
		.tm_year = rtc->tm_year,
		.tm_isdst = 0,
	};

	return timeutil_timegm(&calendar);
}

ZTEST(rtc_calendar, test_counting_across_year)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time requested = {
		.tm_year = 2025 - 1900,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,
		.tm_yday = 364,
		.tm_isdst = -1,
	};
	struct rtc_time observed;
	const int64_t set_seconds = calendar_seconds(&requested);
	const int64_t year_boundary = set_seconds + 5;
	int64_t initial;
	int64_t previous;
	bool reached = false;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC alias device is not ready");
	rc = rtc_set_time(rtc, &requested);
	zassert_equal(rc, 0, "rtc_set_time failed: %d", rc);
	rc = rtc_get_time(rtc, &observed);
	zassert_equal(rc, 0, "Initial rtc_get_time failed: %d", rc);
	initial = calendar_seconds(&observed);
	zassert_true(initial >= set_seconds,
		     "Initial calendar precedes the time just set");
	previous = initial;

	/*
	 * The slowest characterized calendar rate is 17000 / 32000 Hz.
	 * Ten RTC seconds therefore need at most 18.824 physical seconds.
	 * Allow twenty one-second sleeps, checking calendar values after
	 * each sleep. Early completion is allowed; equality between reads
	 * is allowed because the RTC and CPU clocks are independent.
	 *
	 * This is a finite bound of twenty observations and twenty seconds
	 * of requested sleep, with margin over the oscillator bound. It is
	 * not a hard wall-clock execution deadline: interrupt/thread delivery
	 * latency has no supplied upper bound. Delayed execution adds RTC
	 * counting time and is not itself grounds for failing the test.
	 */
	for (int sample = 0; !repair_expired(); ++sample) {
		k_sleep(K_MSEC(1000));
		rc = rtc_get_time(rtc, &observed);
		zassert_equal(rc, 0, "rtc_get_time failed: %d", rc);

		int64_t current = calendar_seconds(&observed);

		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
		if (current - initial >= 10) {
			reached = true;
			break;
		}
	}

	zassert_true(reached,
		     "RTC did not advance ten calendar seconds in twenty sleeps");
	zassert_true(previous >= year_boundary,
		     "RTC calendar did not cross into 2026");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
