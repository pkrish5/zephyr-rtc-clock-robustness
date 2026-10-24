#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <time.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

#define POLL_MS 100
#define MAX_POLLS 200

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static int64_t calendar_seconds(const struct rtc_time *value)
{
	/* Only these two dates belong to this short boundary test. */
	zassert_true((value->tm_year == 125 && value->tm_mon == 11 &&
		      value->tm_mday == 31) ||
		     (value->tm_year == 126 && value->tm_mon == 0 &&
		      value->tm_mday == 1), "Unexpected RTC date");
	zassert_true(value->tm_hour >= 0 && value->tm_hour < 24,
		     "Invalid RTC hour");
	zassert_true(value->tm_min >= 0 && value->tm_min < 60,
		     "Invalid RTC minute");
	zassert_true(value->tm_sec >= 0 && value->tm_sec < 60,
		     "Invalid RTC second");

	struct tm calendar = {
		.tm_year = value->tm_year,
		.tm_mon = value->tm_mon,
		.tm_mday = value->tm_mday,
		.tm_hour = value->tm_hour,
		.tm_min = value->tm_min,
		.tm_sec = value->tm_sec,
		.tm_isdst = 0,
	};

	return (int64_t)timeutil_timegm(&calendar);
}

ZTEST(rtc_calendar, test_lsi_year_boundary)
{
	struct rtc_time seed = {
		.tm_year = 125,
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
	struct rtc_time observed;
	int64_t seeded = calendar_seconds(&seed);
	int64_t boundary = seeded + 5;

	zassert_true(device_is_ready(rtc), "RTC alias device is not ready");
	zassert_equal(rtc_set_time(rtc, &seed), 0, "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");

	int64_t initial = calendar_seconds(&observed);
	int64_t previous = initial;

	zassert_true(initial >= seeded, "Initial calendar precedes set time");
	/* Establish an observed pre-boundary value, not just a set request. */
	zassert_true(initial < boundary,
		     "Initial observation missed the pre-boundary window");

	/*
	 * At 17 kHz, ten RTC seconds take at most
	 * 10 * (128 * 250) / 17000 = 18.824 real seconds.
	 * Allow 200 sleeps of 100 ms (20 seconds of requested waiting).
	 * Poll count, rather than a CPU-uptime deadline, bounds observation:
	 * delayed thread delivery extends waiting and must not shorten the
	 * RTC's opportunity to advance. No hard wall-clock completion bound
	 * is claimed; that would additionally require a scheduling/interrupt
	 * latency bound. Normal kernel timeout delivery is required.
	 */
	for (int i = 0; !repair_expired(); ++i) {
		k_sleep(K_MSEC(POLL_MS));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed at poll %d", i);

		int64_t current = calendar_seconds(&observed);

		zassert_true(current >= previous,
			     "RTC calendar moved backward at poll %d", i);
		previous = current;

		if (current - initial >= 10) {
			zassert_true(current >= boundary &&
				     observed.tm_year == 126,
				     "RTC did not cross the year boundary");
			return;
		}
	}

	zassert_true(false,
		     "RTC failed to advance ten calendar seconds in %d polls",
		     MAX_POLLS);
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
