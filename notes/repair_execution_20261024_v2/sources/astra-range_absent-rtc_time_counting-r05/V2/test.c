#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

/* Calendar seconds relative to 2025-12-31 00:00:00. */
static int32_t calendar_seconds(const struct rtc_time *t)
{
	bool december = t->tm_year == 125 && t->tm_mon == 11 &&
			t->tm_mday == 31;
	bool january = t->tm_year == 126 && t->tm_mon == 0 &&
		       t->tm_mday == 1;

	zassert_true(december || january, "Unexpected calendar date");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24,
		     "Invalid hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60,
		     "Invalid minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60,
		     "Invalid second");

	return (january ? 86400 : 0) + t->tm_hour * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_year_rollover)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time start = {
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
	int32_t initial;
	int32_t previous;
	int32_t current;
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial RTC read failed");

	initial = calendar_seconds(&observed);
	zassert_true(initial >= calendar_seconds(&start) && initial < 86400,
		     "Initial calendar must be near, and before, rollover");
	previous = initial;
	current = initial;

	/*
	 * CPU uptime only bounds observation; progress is measured entirely
	 * from RTC calendar fields. Sixty seconds allows six times the nominal
	 * ten-second interval, comfortably covering STM32F407 LSI frequency
	 * tolerance and polling overhead. Normally this exits after about ten
	 * RTC seconds. Equal reads are expected with 250 ms polling.
	 */
	deadline = repair_deadline;
	while (k_uptime_get() < deadline) {
		k_sleep(K_MSEC(250));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "RTC read failed");
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
		if (current - initial >= 10) {
			break;
		}
	}

	zassert_true(current - initial >= 10,
		     "RTC did not advance ten calendar seconds within 60 seconds");
	zassert_true(observed.tm_year == 126 && observed.tm_mon == 0 &&
		     observed.tm_mday == 1, "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
