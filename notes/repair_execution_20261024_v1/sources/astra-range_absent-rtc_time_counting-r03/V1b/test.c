#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

static bool leap_year(int year)
{
	return (year % 4 == 0) &&
	       ((year % 100 != 0) || (year % 400 == 0));
}

/* Convert validated calendar fields to seconds since 2000-01-01. */
static int64_t calendar_seconds(const struct rtc_time *t)
{
	static const int month_days[] = {
		31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
	};
	int year = t->tm_year + 1900;
	int64_t days = 0;

	zassert_true(year >= 2000 && year <= 2099, "Invalid RTC year");
	zassert_true(t->tm_mon >= 0 && t->tm_mon < 12,
		     "Invalid RTC month");
	int limit = month_days[t->tm_mon] +
		    (t->tm_mon == 1 && leap_year(year));

	zassert_true(t->tm_mday >= 1 && t->tm_mday <= limit,
		     "Invalid RTC day");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24,
		     "Invalid RTC hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60,
		     "Invalid RTC minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60,
		     "Invalid RTC second");

	for (int y = 2000; y < year; ++y) {
		days += leap_year(y) ? 366 : 365;
	}
	for (int m = 0; m < t->tm_mon; ++m) {
		days += month_days[m] + (m == 1 && leap_year(year));
	}
	days += t->tm_mday - 1;
	return days * 86400 + t->tm_hour * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time start = {
		.tm_year = 125, /* 2025 */
		.tm_mon = 11,  /* December */
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,  /* Wednesday */
		.tm_yday = 364,
		.tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time observed;
	int64_t programmed = calendar_seconds(&start);

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");

	int64_t initial = calendar_seconds(&observed);

	/* Allow one tick between programming and the immediate readback. */
	zassert_true(initial >= programmed && initial <= programmed + 1,
		     "Initial calendar does not match programmed time");
	int64_t previous = initial;

	/*
	 * At most 600 sleeps of 100 ms: approximately 60 host seconds.
	 * The independent STM32F407 LSI has a wide frequency tolerance
	 * (17-47 kHz); this leaves ample margin for ten RTC seconds even
	 * at its slow end. No equality with CPU-clock elapsed time is assumed.
	 * Equal consecutive calendar readings are expected and permitted.
	 */
	for (int i = 0; !repair_expired(); ++i) {
		k_sleep(K_MSEC(100));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed during observation");
		int64_t current = calendar_seconds(&observed);

		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
		if (current - initial >= 10) {
			zassert_equal(observed.tm_year, 126, "Wrong year after rollover");
			zassert_equal(observed.tm_mon, 0, "Wrong month after rollover");
			zassert_equal(observed.tm_mday, 1, "Wrong day after rollover");
			return;
		}
	}

	zassert_true(false, "RTC did not advance ten seconds within observation bound");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
