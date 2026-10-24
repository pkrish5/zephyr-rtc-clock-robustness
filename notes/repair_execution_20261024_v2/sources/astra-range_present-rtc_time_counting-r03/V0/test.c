#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#include <stdint.h>
#include <time.h>

#define POLL_MS 250
#define MAX_POLLS 80

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

	zassert_true(rtc->tm_sec >= 0 && rtc->tm_sec <= 59,
		     "Invalid RTC second");
	zassert_true(rtc->tm_min >= 0 && rtc->tm_min <= 59,
		     "Invalid RTC minute");
	zassert_true(rtc->tm_hour >= 0 && rtc->tm_hour <= 23,
		     "Invalid RTC hour");
	zassert_true(rtc->tm_mon >= 0 && rtc->tm_mon <= 11,
		     "Invalid RTC month");
	zassert_true(rtc->tm_mday >= 1 && rtc->tm_mday <= 31,
		     "Invalid RTC day");

	return timeutil_timegm(&calendar);
}

ZTEST(rtc_calendar, test_count_across_year)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time initial = {
		.tm_year = 2025 - 1900,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,
		.tm_yday = 364,
		.tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time observed = {0};
	int64_t programmed = calendar_seconds(&initial);
	int64_t first;
	int64_t previous;
	int64_t current;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	rc = rtc_set_time(rtc, &initial);
	zassert_equal(rc, 0, "rtc_set_time failed: %d", rc);
	rc = rtc_get_time(rtc, &observed);
	zassert_equal(rc, 0, "Initial rtc_get_time failed: %d", rc);

	first = calendar_seconds(&observed);
	zassert_true(first >= programmed,
		     "Initial read precedes the programmed calendar");
	previous = first;
	current = first;

	/*
	 * Slowest calendar rate: 17000 / (128 * 250) = 0.53125 Hz.
	 * Ten calendar seconds therefore require at most 18.824 seconds,
	 * including an arbitrary initial subsecond phase. Eighty sleeps
	 * request 20 seconds in total, providing margin. Repeated calendar
	 * values are expected when polling faster than the RTC ticks.
	 *
	 * This is a finite observation-count bound, not a hard wall-time
	 * deadline: the oscillator specification does not bound interrupt
	 * or thread delivery latency. Delayed execution gives the independent
	 * RTC more time to advance. Normal scheduler progress is required.
	 */
	for (int i = 0; i < MAX_POLLS; ++i) {
		k_sleep(K_MSEC(POLL_MS));
		rc = rtc_get_time(rtc, &observed);
		zassert_equal(rc, 0, "rtc_get_time failed: %d", rc);
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;

		if (current - first >= 10) {
			break;
		}
	}

	zassert_true(current - first >= 10,
		     "RTC did not advance ten seconds within %d observations",
		     MAX_POLLS);
	zassert_true(current - programmed >= 10,
		     "RTC did not advance ten seconds beyond the set time");
	zassert_true(observed.tm_year >= 2026 - 1900,
		     "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
