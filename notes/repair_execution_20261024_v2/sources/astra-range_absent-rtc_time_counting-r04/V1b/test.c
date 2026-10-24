#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

/* Seconds relative to 2025-12-31 00:00:00, across the tested boundary. */
static int64_t calendar_seconds(const struct rtc_time *t)
{
	int day;

	if (t->tm_year == 125 && t->tm_mon == 11 && t->tm_mday == 31) {
		day = 0;
	} else if (t->tm_year == 126 && t->tm_mon == 0 && t->tm_mday == 1) {
		day = 1;
	} else {
		zassert_true(false, "Unexpected calendar date: %d-%d-%d",
			     t->tm_year + 1900, t->tm_mon + 1, t->tm_mday);
		return -1;
	}

	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24, "Invalid hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60, "Invalid minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60, "Invalid second");

	return (int64_t)day * 86400 + t->tm_hour * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_year_rollover)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 125,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,
		.tm_yday = 364,
		.tm_isdst = 0,
		.tm_nsec = 0,
	};
	struct rtc_time observed;
	int64_t first, previous, deadline;
	bool reached = false;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_equal(rtc_set_time(rtc, &initial), 0, "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");

	first = calendar_seconds(&observed);
	zassert_true(first >= calendar_seconds(&initial),
		     "Initial read precedes the programmed calendar");
	zassert_true(first < 86400, "Initial read must precede year rollover");
	previous = first;

	/*
	 * CPU time only limits observation; calendar values prove progress.
	 * With nominal 32 kHz LSI prescaling, even a 17 kHz LSI needs
	 * only about 19 CPU seconds for ten RTC seconds. Allow 60 seconds
	 * for oscillator tolerance, calendar phase and scheduling overhead.
	 * Polling stops immediately once sufficient calendar progress occurs.
	 */
	deadline = repair_deadline;
	while (k_uptime_get() < deadline) {
		int64_t current;

		k_sleep(K_MSEC(100));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed during observation");
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;

		if (current - first >= 10) {
			zassert_equal(observed.tm_year, 126, "Year did not roll over");
			zassert_equal(observed.tm_mon, 0, "Expected January");
			zassert_equal(observed.tm_mday, 1, "Expected January 1");
			reached = true;
			break;
		}
	}

	zassert_true(reached, "RTC did not advance ten calendar seconds within 60 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
