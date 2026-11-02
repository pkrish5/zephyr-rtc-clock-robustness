/* SPDX-License-Identifier: Apache-2.0 */
#include "../common.h"
#include <zephyr/drivers/counter.h>
#include <zephyr/sys/atomic.h>

static const struct device *const dev = DEVICE_DT_GET(DT_ALIAS(rtc_0));
static atomic_t count, event_error;
static uint32_t began, first_count;
static uint32_t token;

static void on_counter(const struct device *which, uint8_t id, uint32_t ticks, void *data)
{
	uint32_t now;
	if (which != dev || id != 0 || data != &token || !k_is_in_isr() ||
	    counter_get_value(which, &now) != 0 || now != ticks ||
	    (uint32_t)(now - first_count) < 2 || ref_elapsed(began) < REF_TWO_TICK_EARLIEST_MS) {
		atomic_set(&event_error, 1);
	}
	atomic_inc(&count);
}
static void prepare(void)
{
	zassert_true(device_is_ready(dev), "counter unavailable");
	zassert_equal(counter_get_num_of_channels(dev), 1, "registered RTC-only channel capability changed");
	zassert_equal(counter_get_frequency(dev), 1, "registered nominal counter frequency changed");
	zassert_ok(counter_cancel_channel_alarm(dev, 0), "clear prior callback state");
	zassert_ok(counter_start(dev), "start counter");
	atomic_set(&count, 0); atomic_set(&event_error, 0);
	zassert_ok(counter_get_value(dev, &first_count), "read starting counter");
	began = k_uptime_get_32();
}
static void wait_for_callback(void)
{
	for (;;) {
		zassert_equal(atomic_get(&event_error), 0, "premature, misidentified, or inconsistent counter callback");
		zassert_true(atomic_get(&count) <= 1, "duplicate counter callback");
		zassert_true(ref_elapsed(began) <= REF_COUNTER_CEILING_MS, "counter reference ceiling");
		if (atomic_get(&count) == 1) { break; }
		k_msleep(REF_POLL_MS);
	}
}
static void finish(void)
{
	zassert_ok(counter_cancel_channel_alarm(dev, 0), "cancel counter alarm");
	zassert_ok(counter_stop(dev), "stop counter");
}
ZTEST(ref_counter, test_all_channels)
{
	struct counter_alarm_cfg config = {.ticks = 2, .callback = on_counter, .user_data = &token};
	prepare();
	zassert_ok(counter_set_channel_alarm(dev, 0, &config), "configure supported channel");
	for (unsigned int id = 1; id < 10; id++) {
		zassert_equal(counter_set_channel_alarm(dev, id, &config), -ENOTSUP, "unsupported channel accepted");
	}
	wait_for_callback();
	printk("REF_EVENT all_channels elapsed_ms=%u\n", ref_elapsed(began));
	for (unsigned int id = 1; id < 10; id++) {
		zassert_equal(counter_cancel_channel_alarm(dev, id), -ENOTSUP, "unsupported cancellation accepted");
	}
	finish();
}
ZTEST(ref_counter, test_single_shot_alarm_notop)
{
	struct counter_alarm_cfg config = {.ticks = 2, .callback = on_counter, .user_data = &token};
	/* Explicit clean state: this diagnoses delivery, not the original cascade. */
	prepare();
	zassert_ok(counter_set_channel_alarm(dev, 0, &config), "clean-state single-shot setup");
	wait_for_callback();
	printk("REF_EVENT single_shot elapsed_ms=%u\n", ref_elapsed(began));
	/* Retain the original three-second additional no-repeat observation. */
	k_msleep(3000);
	zassert_equal(atomic_get(&count), 1, "single-shot repeated");
	zassert_equal(atomic_get(&event_error), 0, "single-shot callback error");
	finish();
}
ZTEST_SUITE(ref_counter, NULL, NULL, NULL, NULL, NULL);
