#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

#define RTC_NODE DT_ALIAS(rtc)

static int calendar_seconds(const struct rtc_time *t)
{
	int day;

	if (t->tm_year == 123 && t->tm_mon == 11 && t->tm_mday == 31) {
		day = 0;
	} else if (t->tm_year == 124 && t->tm_mon == 0 && t->tm_mday == 1) {
		day = 1;
	} else {
		return -1;
	}

	if (t->tm_hour < 0 || t->tm_hour > 23 ||
	    t->tm_min < 0 || t->tm_min > 59 ||
	    t->tm_sec < 0 || t->tm_sec > 59) {
		return -1;
	}

	return day * 86400 + t->tm_hour * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
	struct rtc_time set = {
		.tm_year = 123, /* 2023, measured from 1900 */
		.tm_mon = 11,   /* December, measured from zero */
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 0,
		.tm_yday = 364,
		.tm_isdst = 0,
	};
	struct rtc_time read;
	int initial, previous, current;
	bool reached = false;

	zassert_true(device_is_ready(rtc));
	zassert_equal(rtc_set_time(rtc, &set), 0);
	zassert_equal(rtc_get_time(rtc, &read), 0);
	initial = calendar_seconds(&read);
	zassert_true(initial >= 86395 && initial < 86400);
	previous = initial;

	/* Thirty seconds allows margin for LSI frequency variation. */
	for (int i = 0; !repair_expired(); ++i) {
		k_sleep(K_MSEC(1000));
		zassert_equal(rtc_get_time(rtc, &read), 0);
		current = calendar_seconds(&read);
		zassert_true(current >= previous);
		previous = current;
		if (current >= 86400 && current >= initial + 10) {
			reached = true;
			break;
		}
	}

	zassert_true(reached);
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
