/* SPDX-License-Identifier: Apache-2.0 */
#include "common.h"

static atomic_t delivered, event_error;
static uint32_t began, first_count, requested, target_count, callback_elapsed, token;

static void on_alarm(const struct device *which, uint8_t channel, uint32_t ticks, void *data)
{
	uint32_t now = 0;
	uint32_t early = requested == 1 ? VERIFY_ONE_EARLIEST_MS : VERIFY_TWO_EARLIEST_MS;
	callback_elapsed = elapsed_ms(began);
	if (which != verify_dev || channel != 0 || data != &token || !k_is_in_isr() ||
	    counter_get_value(which, &now) != 0 || now != ticks ||
	    (uint32_t)(now - first_count) < requested || callback_elapsed < early ||
	    (uint32_t)atomic_get(&delivered) >= target_count) {
		atomic_set(&event_error, 1);
	}
	atomic_inc(&delivered);
}

static void before(void *fixture)
{
	ARG_UNUSED(fixture);
	require_counter();
	zassert_ok(counter_cancel_channel_alarm(verify_dev, 0), "clear previous callback");
	zassert_ok(counter_stop(verify_dev), "stop previous counter state");
	atomic_set(&delivered, 0);
	atomic_set(&event_error, 0);
	zassert_ok(counter_start(verify_dev), "start counter");
}

static void after(void *fixture)
{
	ARG_UNUSED(fixture);
	/* Attempt both cleanup operations even when a case assertion failed. */
	int cancel = counter_cancel_channel_alarm(verify_dev, 0);
	int stop = counter_stop(verify_dev);
	zassert_ok(cancel, "reference cleanup cancellation");
	zassert_ok(stop, "reference cleanup stop");
}

static void begin_request(uint32_t ticks)
{
	requested = ticks;
	target_count = (uint32_t)atomic_get(&delivered) + 1U;
	zassert_ok(counter_get_value(verify_dev, &first_count), "read counter before request");
	began = k_uptime_get_32();
}

static void wait_request(void)
{
	uint32_t ceiling = requested == 1 ? VERIFY_ONE_CEILING_MS : VERIFY_TWO_CEILING_MS;
	for (;;) {
		zassert_equal(atomic_get(&event_error), 0, "premature, misidentified or inconsistent callback");
		zassert_true((uint32_t)atomic_get(&delivered) <= target_count, "duplicate callback");
		zassert_true(elapsed_ms(began) <= ceiling, "reference wait ceiling");
		if ((uint32_t)atomic_get(&delivered) == target_count) { break; }
		k_msleep(VERIFY_POLL_MS);
	}
}

ZTEST(ref_counter_verify, test_a_all_channels)
{
	struct counter_alarm_cfg config = {.ticks = 2, .callback = on_alarm, .user_data = &token};
	begin_request(2);
	zassert_ok(counter_set_channel_alarm(verify_dev, 0, &config), "supported alarm setup");
	for (unsigned int id = 1; id < 10; id++) {
		zassert_equal(counter_set_channel_alarm(verify_dev, id, &config), -ENOTSUP, "unsupported channel accepted");
	}
	wait_request();
	zassert_equal(atomic_get(&delivered), 1, "all-channels count");
	printk("VERIFY_EVENT all_channels callback_elapsed_ms=%u count=%u\n", callback_elapsed, (unsigned int)atomic_get(&delivered));
	for (unsigned int id = 1; id < 10; id++) {
		zassert_equal(counter_cancel_channel_alarm(verify_dev, id), -ENOTSUP, "unsupported cancellation accepted");
	}
}

ZTEST(ref_counter_verify, test_b_short_relative_alarm)
{
	struct counter_alarm_cfg config = {.ticks = 1, .callback = on_alarm, .user_data = &token};
	uint32_t shortest = UINT32_MAX, longest = 0;
	for (unsigned int i = 0; i < 100; i++) {
		begin_request(1);
		zassert_ok(counter_set_channel_alarm(verify_dev, 0, &config), "sequential one-tick alarm setup");
		wait_request();
		zassert_equal((uint32_t)atomic_get(&delivered), i + 1U, "sequential callback count");
		shortest = MIN(shortest, callback_elapsed);
		longest = MAX(longest, callback_elapsed);
		/* No manual cancellation between requests: require automatic rearmability. */
	}
	printk("VERIFY_EVENT short_relative requests=100 count=%u min_callback_ms=%u max_callback_ms=%u\n",
	       (unsigned int)atomic_get(&delivered), shortest, longest);
}

ZTEST(ref_counter_verify, test_c_single_shot_alarm_notop)
{
	struct counter_alarm_cfg config = {.ticks = 2, .callback = on_alarm, .user_data = &token};
	begin_request(2);
	zassert_ok(counter_set_channel_alarm(verify_dev, 0, &config), "clean single-shot alarm setup");
	wait_request();
	printk("VERIFY_EVENT single_shot callback_elapsed_ms=%u count=%u\n", callback_elapsed, (unsigned int)atomic_get(&delivered));
	k_msleep(3000);
	zassert_equal(atomic_get(&delivered), 1, "single-shot repeated");
	zassert_equal(atomic_get(&event_error), 0, "single-shot callback error");
}
ZTEST_SUITE(ref_counter_verify, NULL, NULL, before, after, NULL);
