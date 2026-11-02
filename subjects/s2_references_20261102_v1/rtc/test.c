/* SPDX-License-Identifier: Apache-2.0 */
#include "../common.h"
#include <zephyr/drivers/rtc.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/timeutil.h>
#include <time.h>

static const struct device *const dev = DEVICE_DT_GET(DT_ALIAS(rtc));
#define CHANNELS DT_PROP(DT_ALIAS(rtc), alarms_count)
#define MASK (RTC_ALARM_TIME_MASK_SECOND | RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)
static const struct rtc_time start_time = {
	.tm_sec = 55, .tm_min = 59, .tm_hour = 23, .tm_mday = 31,
	.tm_mon = 11, .tm_year = 124, .tm_wday = 2, .tm_yday = 365,
	.tm_isdst = -1, .tm_nsec = 0,
};
static const struct rtc_time target_time = {
	.tm_sec = 5, .tm_min = 0, .tm_hour = 0, .tm_mday = 1,
	.tm_mon = 0, .tm_year = 125, .tm_wday = 3, .tm_yday = 0,
	.tm_isdst = -1, .tm_nsec = 0,
};
static int64_t seconds_of(const struct rtc_time *time)
{
	struct tm copy = {
		.tm_sec = time->tm_sec, .tm_min = time->tm_min, .tm_hour = time->tm_hour,
		.tm_mday = time->tm_mday, .tm_mon = time->tm_mon, .tm_year = time->tm_year,
		.tm_isdst = -1,
	};
	return timeutil_timegm(&copy);
}
static void clear_alarms(void)
{
	zassert_true(device_is_ready(dev), "RTC unavailable");
	for (unsigned int id = 0; id < CHANNELS; id++) {
		zassert_ok(rtc_alarm_set_callback(dev, id, NULL, NULL), "clear callback");
		zassert_ok(rtc_alarm_set_time(dev, id, 0, NULL), "disable alarm");
		zassert_true(rtc_alarm_is_pending(dev, id) >= 0, "clear pending");
	}
}
static void set_and_readback_alarms(void)
{
	for (unsigned int id = 0; id < CHANNELS; id++) {
		uint16_t supported, actual_mask;
		struct rtc_time actual;
		zassert_ok(rtc_alarm_get_supported_fields(dev, id, &supported), "supported fields");
		zassert_equal(MASK & ~supported, 0, "required alarm fields unavailable");
		zassert_ok(rtc_alarm_set_time(dev, id, MASK, &target_time), "program alarm");
		zassert_ok(rtc_alarm_get_time(dev, id, &actual_mask, &actual), "read back alarm");
		zassert_equal(actual_mask, MASK, "alarm mask changed");
		zassert_equal(actual.tm_sec, target_time.tm_sec, "alarm second changed");
		zassert_equal(actual.tm_min, target_time.tm_min, "alarm minute changed");
		zassert_equal(actual.tm_hour, target_time.tm_hour, "alarm hour changed");
	}
}

ZTEST(ref_rtc, test_a_alarm_pending)
{
	clear_alarms();
	/* Both channels and the two original time-reset repetitions are retained. */
	for (int repetition = 0; repetition < 2; repetition++) {
		bool seen[CHANNELS] = {false};
		uint32_t began = k_uptime_get_32();
		zassert_ok(rtc_set_time(dev, &start_time), "set calendar");
		set_and_readback_alarms();
		for (unsigned int id = 0; id < CHANNELS; id++) {
			zassert_ok(rtc_alarm_is_pending(dev, id), "pending before target");
		}
		for (;;) {
			unsigned int complete = 0;
			for (unsigned int id = 0; id < CHANNELS; id++) {
				int pending = rtc_alarm_is_pending(dev, id);
				zassert_true(pending >= 0, "pending read failed");
				if (pending == 1) {
					struct rtc_time now;
					zassert_false(seen[id], "duplicate pending event");
					zassert_ok(rtc_get_time(dev, &now), "calendar read");
					zassert_true(seconds_of(&now) >= seconds_of(&target_time), "premature pending calendar");
					zassert_true(ref_elapsed(began) >= REF_TEN_TICK_EARLIEST_MS, "premature independent-time pending");
					seen[id] = true;
				}
				complete += seen[id];
			}
			zassert_true(ref_elapsed(began) <= REF_TEN_TICK_CEILING_MS, "pending reference ceiling");
			if (complete == CHANNELS) { break; }
			k_msleep(REF_POLL_MS);
		}
		printk("REF_EVENT pending repetition=%d elapsed_ms=%u\n", repetition, ref_elapsed(began));
	}
	clear_alarms();
}

static atomic_t callback_count[CHANNELS];
static atomic_t callback_error;
static uint32_t callback_began;
static void on_alarm(const struct device *which, uint16_t id, void *data)
{
	struct rtc_time now;
	if (which != dev || id >= CHANNELS || (uintptr_t)data != id ||
	    rtc_get_time(which, &now) != 0 || seconds_of(&now) < seconds_of(&target_time) ||
	    ref_elapsed(callback_began) < REF_TEN_TICK_EARLIEST_MS) {
		atomic_set(&callback_error, 1);
	} else {
		atomic_inc(&callback_count[id]);
	}
}
ZTEST(ref_rtc, test_b_alarm_callback)
{
	clear_alarms();
	for (int repetition = 0; repetition < 2; repetition++) {
		atomic_set(&callback_error, 0);
		for (unsigned int id = 0; id < CHANNELS; id++) { atomic_set(&callback_count[id], 0); }
		callback_began = k_uptime_get_32();
		zassert_ok(rtc_set_time(dev, &start_time), "set calendar");
		set_and_readback_alarms();
		for (unsigned int id = 0; id < CHANNELS; id++) {
			zassert_ok(rtc_alarm_set_callback(dev, id, on_alarm, (void *)(uintptr_t)id), "set callback");
		}
		for (;;) {
			unsigned int complete = 0;
			zassert_equal(atomic_get(&callback_error), 0, "premature or misidentified callback");
			for (unsigned int id = 0; id < CHANNELS; id++) {
				atomic_val_t count = atomic_get(&callback_count[id]);
				zassert_true(count <= 1, "duplicate callback");
				complete += count == 1;
			}
			zassert_true(ref_elapsed(callback_began) <= REF_TEN_TICK_CEILING_MS, "callback reference ceiling");
			if (complete == CHANNELS) { break; }
			k_msleep(REF_POLL_MS);
		}
		printk("REF_EVENT callback repetition=%d elapsed_ms=%u\n", repetition, ref_elapsed(callback_began));
		clear_alarms();
	}
}

ZTEST(ref_rtc, test_c_time_counting)
{
	/* Original counting date and exact ten-second target, not the alarm date. */
	time_t initial = 1767225595;
	struct tm native;
	struct rtc_time start = {0};
	int64_t previous = initial;
	gmtime_r(&initial, &native);
	start.tm_sec = native.tm_sec; start.tm_min = native.tm_min;
	start.tm_hour = native.tm_hour; start.tm_mday = native.tm_mday;
	start.tm_mon = native.tm_mon; start.tm_year = native.tm_year;
	start.tm_wday = native.tm_wday; start.tm_yday = native.tm_yday;
	start.tm_isdst = -1;
	clear_alarms();
	uint32_t began = k_uptime_get_32();
	zassert_ok(rtc_set_time(dev, &start), "set counting calendar");
	for (;;) {
		struct rtc_time now;
		zassert_ok(rtc_get_time(dev, &now), "read counting calendar");
		int64_t current = seconds_of(&now);
		zassert_true(current >= previous, "calendar went backwards");
		zassert_true(ref_elapsed(began) <= REF_TEN_TICK_CEILING_MS, "counting reference ceiling");
		if (current >= initial + 10) {
			zassert_equal(current, initial + 10, "missed exact ten-second target");
			zassert_true(ref_elapsed(began) >= REF_TEN_TICK_EARLIEST_MS, "premature counting transition");
			break;
		}
		previous = current;
		k_msleep(REF_POLL_MS);
	}
	printk("REF_EVENT counting elapsed_ms=%u\n", ref_elapsed(began));
}
ZTEST_SUITE(ref_rtc, NULL, NULL, NULL, NULL, NULL);
