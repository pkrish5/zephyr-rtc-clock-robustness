#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

/* Seconds since 2023-12-31 23:59:55, for dates this test can observe. */
static int seconds_from_start(const struct rtc_time *t)
{
	int seconds = t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;

	if (t->tm_year == 123 && t->tm_mon == 11 && t->tm_mday == 31) {
		return seconds - (23 * 3600 + 59 * 60 + 55);
	}
	if (t->tm_year == 124 && t->tm_mon == 0 && t->tm_mday == 1) {
		return seconds + 5;
	}
	return -1;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time start = {
		.tm_year = 123, /* 2023: years since 1900 */
		.tm_mon = 11,   /* December: months since January */
		.tm_mday = 31,
		.tm_wday = 0,   /* Sunday */
		.tm_yday = 364,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
	};
	struct rtc_time observed;
	int previous;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0, "initial RTC read failed");
	previous = seconds_from_start(&observed);
	zassert_true(previous >= 0 && previous <= 2,
		     "initial calendar does not match the set time");

	/* Allow 60 wall-clock seconds for ten independent LSI-driven RTC ticks. */
	for (int i = 0; !repair_expired() && previous < 10; i++) {
		int current;

		k_sleep(K_MSEC(100));
		zassert_equal(rtc_get_time(rtc, &observed), 0, "RTC read failed");
		current = seconds_from_start(&observed);
		zassert_true(current >= previous,
			     "RTC calendar moved backward or left the expected dates");
		previous = current;
	}

	zassert_true(previous >= 10, "RTC did not advance ten calendar seconds");
	zassert_true(observed.tm_year == 124 && observed.tm_mon == 0 &&
		     observed.tm_mday == 1, "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
