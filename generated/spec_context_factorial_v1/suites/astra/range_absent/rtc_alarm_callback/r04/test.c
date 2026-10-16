#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

BUILD_ASSERT(ALARM_MASK == 7);

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static K_SEM_DEFINE(events, 0, 2);

static struct callback_state {
	atomic_t count;
	atomic_t reported_id;
} callbacks[2];

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
	struct callback_state *state = user_data;

	ARG_UNUSED(dev);
	atomic_set(&state->reported_id, id);
	atomic_inc(&state->count);
	k_sem_give(&events);
}

/* Seconds since the initial calendar time, restricted to this test window. */
static int elapsed_rtc_seconds(const struct rtc_time *time)
{
	if (time->tm_year == 124 && time->tm_mon == 11 &&
	    time->tm_mday == 31 && time->tm_hour == 23 &&
	    time->tm_min == 59 && time->tm_sec >= 55 && time->tm_sec <= 59) {
		return time->tm_sec - 55;
	}
	if (time->tm_year == 125 && time->tm_mon == 0 &&
	    time->tm_mday == 1 && time->tm_hour == 0 &&
	    time->tm_min == 0 && time->tm_sec >= 0 && time->tm_sec <= 59) {
		return 5 + time->tm_sec;
	}
	return -1;
}

static void cleanup(void *fixture)
{
	ARG_UNUSED(fixture);
	if (!device_is_ready(rtc)) {
		return;
	}
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
	}
}

ZTEST(rtc_alarms, test_year_rollover)
{
	struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	};
	struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	};
	bool observed[2] = { false, false };

	zassert_true(device_is_ready(rtc), "RTC alias is not ready");
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		/* Reading pending status clears any old pending indication. */
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0);
		atomic_set(&callbacks[id].count, 0);
		atomic_set(&callbacks[id].reported_id, -1);
	}
	k_sem_reset(&events);
	zassert_ok(rtc_set_time(rtc, &start));

	/*
	 * Ten RTC seconds can take about 19 wall seconds with the F407 LSI
	 * at its 17 kHz minimum versus 32 kHz nominal. Thirty seconds allows
	 * additional setup and scheduling margin. Judge alarm timing using
	 * the RTC calendar, not a nominal ten-second kernel sleep.
	 */
	int64_t deadline = k_uptime_get() + 30000;

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
		                                &callbacks[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
	}

	while (!(observed[0] && observed[1])) {
		struct rtc_time now;
		atomic_val_t counts[2];

		zassert_true(k_uptime_get() < deadline,
		             "Timed out waiting for both RTC callbacks");
		(void)k_sem_take(&events, K_MSEC(10));

		/* Snapshot events before reading the calendar, so an interrupt
		 * after the calendar read cannot be mistaken for an early alarm.
		 */
		counts[0] = atomic_get(&callbacks[0].count);
		counts[1] = atomic_get(&callbacks[1].count);
		zassert_ok(rtc_get_time(rtc, &now));
		int elapsed = elapsed_rtc_seconds(&now);

		zassert_true(elapsed >= 0, "Unexpected RTC calendar");
		for (uint16_t id = 0; id < 2; ++id) {
			zassert_true(counts[id] <= 1, "Duplicate callback on %u", id);
			if (elapsed < 10) {
				zassert_equal(counts[id], 0,
				              "Alarm %u observed prematurely", id);
			}
			if (counts[id] && !observed[id]) {
				zassert_equal(elapsed, 10,
				              "Alarm %u observed outside 00:00:05", id);
				zassert_equal(atomic_get(&callbacks[id].reported_id), id,
				              "Incorrect callback alarm ID");
				observed[id] = true;
			}
		}
		zassert_true(elapsed <= 10, "Alarm time passed without both callbacks");
	}
}

ZTEST_SUITE(rtc_alarms, NULL, NULL, NULL, cleanup, NULL);
