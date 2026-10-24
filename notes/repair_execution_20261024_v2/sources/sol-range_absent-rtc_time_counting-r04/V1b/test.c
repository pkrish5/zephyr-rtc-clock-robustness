#include <limits.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

/* Seconds since 2024-12-31 23:59:55, for the dates this test observes. */
static int calendar_seconds(const struct rtc_time *t)
{
	if (t->tm_hour < 0 || t->tm_hour > 23 ||
	    t->tm_min < 0 || t->tm_min > 59 ||
	    t->tm_sec < 0 || t->tm_sec > 59) {
		return INT_MIN;
	}

	if (t->tm_year == 124 && t->tm_mon == 11 && t->tm_mday == 31) {
		return (t->tm_hour - 23) * 3600 +
		       (t->tm_min - 59) * 60 + t->tm_sec - 55;
	}
	if (t->tm_year == 125 && t->tm_mon == 0 && t->tm_mday == 1) {
		return 5 + t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;
	}

	return INT_MIN;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 124, /* 2024: years since 1900 */
		.tm_mon = 11,   /* December: zero-based month */
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 2,
		.tm_yday = 365,
	};
	struct rtc_time observed;
	int previous;
	bool crossed = false;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_equal(rtc_set_time(rtc, &initial), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0, "initial RTC read failed");
	previous = calendar_seconds(&observed);
	zassert_true(previous >= 0 && previous <= 2,
		     "initial calendar read differs from the set time");

	/* Up to 25 CPU seconds allows ample margin for LSI clock variation. */
	for (int i = 0; !repair_expired() && previous < 10; ++i) {
		int current;

		k_sleep(K_MSEC(250));
		zassert_equal(rtc_get_time(rtc, &observed), 0, "RTC read failed");
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		crossed |= observed.tm_year == 125 && observed.tm_mon == 0 &&
			   observed.tm_mday == 1;
		previous = current;
	}

	zassert_true(crossed, "RTC did not cross the year boundary");
	zassert_true(previous >= 10, "RTC did not advance ten calendar seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
