#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

static int64_t calendar_seconds(const struct rtc_time *t)
{
	static const int days_per_month[] =
		{ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
	int64_t days = 0;
	int year = t->tm_year + 1900;
	int month = t->tm_mon;
	int leap;

	zassert_true(year >= 2000 && year <= 2099, "invalid RTC year");
	zassert_true(month >= 0 && month < 12, "invalid RTC month");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24 &&
		     t->tm_min >= 0 && t->tm_min < 60 &&
		     t->tm_sec >= 0 && t->tm_sec < 60,
		     "invalid RTC time");

	for (int y = 2000; y < year; y++) {
		days += ((y % 4) == 0) ? 366 : 365;
	}
	leap = (year % 4) == 0;
	for (int m = 0; m < month; m++) {
		days += days_per_month[m] + (m == 1 && leap);
	}
	zassert_true(t->tm_mday >= 1 &&
		     t->tm_mday <= days_per_month[month] + (month == 1 && leap),
		     "invalid RTC day");

	return ((days + t->tm_mday - 1) * 24 + t->tm_hour) * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_counts_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time set = {
		.tm_year = 124, /* 2024 */
		.tm_mon = 11,   /* December */
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
	};
	struct rtc_time first;
	struct rtc_time current;
	int64_t previous;
	int64_t target;
	bool reached = false;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_ok(rtc_set_time(rtc, &set), "RTC set failed");
	zassert_ok(rtc_get_time(rtc, &first), "initial RTC read failed");
	zassert_equal(first.tm_year, 124, "initial RTC year differs");
	zassert_equal(first.tm_mon, 11, "initial RTC month differs");
	zassert_equal(first.tm_mday, 31, "initial RTC day differs");
	zassert_equal(first.tm_hour, 23, "initial RTC hour differs");
	zassert_equal(first.tm_min, 59, "initial RTC minute differs");
	zassert_true(first.tm_sec >= 55 && first.tm_sec <= 59,
		     "initial RTC second differs");

	previous = calendar_seconds(&first);
	target = previous + 10;

	/* 45 seconds allows for LSI frequency tolerance and scheduling delay. */
	for (int i = 0; i < 450; i++) {
		int64_t now;

		k_sleep(K_MSEC(100));
		zassert_ok(rtc_get_time(rtc, &current), "RTC read failed");
		now = calendar_seconds(&current);
		zassert_true(now >= previous, "RTC calendar moved backward");
		previous = now;
		if (now >= target && current.tm_year >= 125) {
			reached = true;
			break;
		}
	}

	zassert_true(reached, "RTC did not cross the year boundary and advance ten seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
