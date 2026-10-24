#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

static uint64_t calendar_key(const struct rtc_time *t)
{
	uint64_t key = (uint64_t)t->tm_year;

	key = key * 12 + (uint64_t)t->tm_mon;
	key = key * 31 + (uint64_t)t->tm_mday;
	key = key * 24 + (uint64_t)t->tm_hour;
	key = key * 60 + (uint64_t)t->tm_min;
	return key * 60 + (uint64_t)t->tm_sec;
}

static void check_calendar(const struct rtc_time *t)
{
	zassert_true(t->tm_year >= 100 && t->tm_year <= 199);
	zassert_true(t->tm_mon >= 0 && t->tm_mon <= 11);
	zassert_true(t->tm_mday >= 1 && t->tm_mday <= 31);
	zassert_true(t->tm_hour >= 0 && t->tm_hour <= 23);
	zassert_true(t->tm_min >= 0 && t->tm_min <= 59);
	zassert_true(t->tm_sec >= 0 && t->tm_sec <= 59);
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time start = {
		.tm_year = 123, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 0, .tm_yday = 364,
	};
	const struct rtc_time target = {
		.tm_year = 124, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time observed;
	uint64_t previous;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0, "initial RTC read failed");
	check_calendar(&observed);
	previous = calendar_key(&observed);
	zassert_true(previous >= calendar_key(&start), "initial RTC time precedes set time");

	/* 300 x 100 ms allows 30 s. At 17 kHz with a 32000-cycle
	 * prescaler, the calendar advances at least 15 RTC seconds.
	 * Polling avoids reliance on interrupt delivery latency.
	 */
	for (int i = 0; !repair_expired(); ++i) {
		k_sleep(K_MSEC(100));
		zassert_equal(rtc_get_time(rtc, &observed), 0, "RTC read failed");
		check_calendar(&observed);
		uint64_t current = calendar_key(&observed);

		zassert_true(current >= previous, "RTC calendar moved backward");
		if (current >= calendar_key(&target)) {
			return;
		}
		previous = current;
	}

	zassert_true(false, "RTC did not cross the year boundary and advance 10 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
