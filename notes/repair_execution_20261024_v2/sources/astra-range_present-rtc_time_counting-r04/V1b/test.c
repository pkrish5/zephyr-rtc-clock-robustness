#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

#define POLL_MS 100
#define MAX_POLLS 240

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static bool leap_year(int year)
{
	return (year % 4 == 0) && ((year % 100 != 0) || (year % 400 == 0));
}

/* Convert validated calendar fields to seconds since 2000-01-01. */
static int64_t calendar_seconds(const struct rtc_time *t)
{
	static const int month_days[] = {
		31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
	};
	int year;
	int days_in_month;
	int64_t days = 0;

	zassert_true(t->tm_year >= 100 && t->tm_year <= 199,
		     "RTC year outside STM32 calendar range");
	zassert_true(t->tm_mon >= 0 && t->tm_mon < 12, "Invalid month");
	year = t->tm_year + 1900;
	days_in_month = month_days[t->tm_mon] +
		((t->tm_mon == 1 && leap_year(year)) ? 1 : 0);
	zassert_true(t->tm_mday >= 1 && t->tm_mday <= days_in_month,
		     "Invalid day");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24, "Invalid hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60, "Invalid minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60, "Invalid second");

	for (int y = 2000; y < year; ++y) {
		days += leap_year(y) ? 366 : 365;
	}
	for (int m = 0; m < t->tm_mon; ++m) {
		days += month_days[m];
		if (m == 1 && leap_year(year)) {
			++days;
		}
	}
	days += t->tm_mday - 1;
	return ((days * 24 + t->tm_hour) * 60 + t->tm_min) * 60 +
		t->tm_sec;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct rtc_time start = {
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
	int64_t programmed = calendar_seconds(&start);
	int64_t initial;
	int64_t previous;
	bool advanced = false;

	zassert_true(device_is_ready(rtc), "RTC alias device is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");
	initial = calendar_seconds(&observed);
	zassert_true(initial >= programmed, "Initial calendar precedes set time");
	previous = initial;

	/*
	 * At 17 kHz with a 128 * 250 divider, ten RTC seconds require
	 * at most 10 * 32000 / 17000 = 18.824 real seconds. Request up
	 * to 24 seconds of sleep, allowing ample calendar-phase margin.
	 * The 47 kHz extreme merely reaches the target sooner.
	 *
	 * Bound observations, not elapsed uptime: there are at most 240
	 * sleeps and subsequent reads. ISR/thread delivery can extend a
	 * sleep while the independent RTC keeps running. No hard wall-time
	 * completion bound is claimed without a scheduling-latency bound.
	 */
	for (int i = 0; !repair_expired(); ++i) {
		int64_t current;

		k_sleep(K_MSEC(POLL_MS));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed at observation %d", i);
		current = calendar_seconds(&observed);
		zassert_true(current >= previous,
			     "RTC calendar moved backward at observation %d", i);
		previous = current;
		if (current - initial >= 10) {
			advanced = true;
			break;
		}
	}

	zassert_true(advanced, "RTC did not advance ten calendar seconds");
	/* Five seconds after the programmed value is 2026-01-01 midnight. */
	zassert_true(previous >= programmed + 5 && observed.tm_year >= 126,
		     "RTC did not cross the programmed year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
