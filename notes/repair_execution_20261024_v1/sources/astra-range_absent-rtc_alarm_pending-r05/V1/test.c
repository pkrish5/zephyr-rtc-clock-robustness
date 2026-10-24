#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

/* Compare calendar fields; weekday, yearday and subseconds are irrelevant. */
static int calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday,
			  a->tm_hour, a->tm_min, a->tm_sec};
	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday,
			  b->tm_hour, b->tm_min, b->tm_sec};

	for (unsigned int i = 0; i < sizeof(av) / sizeof(av[0]); ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	const struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	const struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	const uint16_t mask = RTC_ALARM_TIME_MASK_SECOND |
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR;
	struct rtc_time readback = {0};
	uint16_t readback_mask = 0;
	bool saw_before = false;
	bool saw_pending = false;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(mask, 7, "Unexpected alarm mask");

	/* Isolate alarm 0 and consume any old pending state on both channels. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
			   "Cannot disable alarm %u", (unsigned int)id);
		int pending = rtc_alarm_is_pending(rtc, id);

		zassert_true(pending == 0 || pending == 1,
			     "Cannot clear pending state: %d", pending);
	}

	zassert_ok(rtc_set_time(rtc, &start), "Cannot set calendar");
	/* Target is 10 RTC seconds away. Allow another 5 seconds for tick
	 * phase, polling and scheduling; uptime bounds even a stopped RTC.
	 */
	const int64_t deadline = repair_deadline;

	zassert_ok(rtc_alarm_set_time(rtc, 0, mask, &target),
		   "Cannot configure alarm");
	zassert_ok(rtc_alarm_get_time(rtc, 0, &readback_mask, &readback),
		   "Cannot read alarm");
	zassert_equal(readback_mask, mask, "Alarm mask mismatch");
	/* Only the enabled alarm fields have defined readback values. */
	zassert_equal(readback.tm_sec, target.tm_sec, "Second mismatch");
	zassert_equal(readback.tm_min, target.tm_min, "Minute mismatch");
	zassert_equal(readback.tm_hour, target.tm_hour, "Hour mismatch");

	while (k_uptime_get() < deadline) {
		struct rtc_time now;
		int pending = rtc_alarm_is_pending(rtc, 0);

		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
		/* Read the calendar after pending to avoid falsely rejecting an
		 * alarm when the target tick occurs between these two calls.
		 * Pending queries may consume the event, so retain this result.
		 */
		zassert_ok(rtc_get_time(rtc, &now), "Cannot read calendar");
		if (calendar_cmp(&now, &target) < 0) {
			saw_before = true;
			zassert_equal(pending, 0, "Alarm pending before target");
		} else if (pending == 1) {
			saw_pending = true;
			break;
		}
		k_msleep(20);
	}

	zassert_ok(rtc_alarm_set_time(rtc, 0, 0, NULL),
		   "Cannot disable tested alarm");
	zassert_true(saw_before, "No observation before target time");
	zassert_true(saw_pending,
		     "No pending alarm at/after target within 15 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
