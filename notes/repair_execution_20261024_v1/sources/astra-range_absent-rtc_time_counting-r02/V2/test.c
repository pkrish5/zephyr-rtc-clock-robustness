#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

#define OBSERVATION_MS 40000
#define POLL_MS 100
#define SECONDS_PER_DAY 86400

/* Seconds since 2025-12-31 00:00:00, for the two expected dates. */
static int32_t calendar_seconds(const struct rtc_time *t)
{
	bool december = t->tm_year == 125 && t->tm_mon == 11 &&
			t->tm_mday == 31;
	bool january = t->tm_year == 126 && t->tm_mon == 0 &&
		       t->tm_mday == 1;

	zassert_true(december || january, "Unexpected RTC date");
	zassert_true(t->tm_hour >= 0 && t->tm_hour <= 23,
		     "Invalid RTC hour");
	zassert_true(t->tm_min >= 0 && t->tm_min <= 59,
		     "Invalid RTC minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec <= 59,
		     "Invalid RTC second");

	return (january ? SECONDS_PER_DAY : 0) +
	       t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_count_through_new_year)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time requested = {
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
	struct rtc_time observed = {0};
	int32_t initial;
	int32_t previous;
	int32_t current;
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_equal(rtc_set_time(rtc, &requested), 0,
		      "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");

	initial = calendar_seconds(&observed);
	zassert_true(initial >= calendar_seconds(&requested) &&
		     initial < SECONDS_PER_DAY,
		     "Initial read must reflect the set time before midnight");
	previous = initial;
	current = initial;

	/*
	 * LSI is independent of the CPU clock: do not demand one RTC second
	 * per uptime second. Its approximately 17--47 kHz range, versus
	 * nominal 32 kHz, allows ten RTC seconds to take about 19 real
	 * seconds. Forty seconds provides ample phase and scheduling margin.
	 * Uptime only bounds observation; progress is measured by calendar.
	 */
	deadline = repair_deadline;
	while (k_uptime_get() < deadline) {
		k_sleep(K_MSEC(POLL_MS));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed during observation");
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
		if (current - initial >= 10) {
			break;
		}
	}

	zassert_true(current - initial >= 10,
		     "RTC did not advance ten calendar seconds within 40 seconds");
	zassert_true(observed.tm_year == 126 && observed.tm_mon == 0 &&
		     observed.tm_mday == 1, "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
