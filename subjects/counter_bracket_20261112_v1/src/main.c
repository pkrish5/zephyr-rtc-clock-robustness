/* SPDX-License-Identifier: Apache-2.0 */
#include <zephyr/device.h>
#include <zephyr/drivers/counter.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

static const struct device *const rtc_counter = DEVICE_DT_GET(DT_ALIAS(rtc_0));

ZTEST(ref_counter_bracket, test_rate_window)
{
	uint32_t v0, v1, a0, b0, a1, b1;
	zassert_true(device_is_ready(rtc_counter), "RTC-only counter unavailable");
	zassert_equal(counter_get_num_of_channels(rtc_counter), 1,
		      "counter capability changed");
	zassert_equal(counter_get_frequency(rtc_counter), 1,
		      "nominal divider policy changed");
	zassert_ok(counter_cancel_channel_alarm(rtc_counter, 0), "clear alarm");
	zassert_ok(counter_stop(rtc_counter), "clean stop");
	zassert_ok(counter_start(rtc_counter), "start counter");
	a0 = k_uptime_get_32();
	zassert_ok(counter_get_value(rtc_counter, &v0), "first counter read");
	b0 = k_uptime_get_32();
	k_msleep(10000);
	a1 = k_uptime_get_32();
	zassert_ok(counter_get_value(rtc_counter, &v1), "second counter read");
	b1 = k_uptime_get_32();
	printk("BRACKET a0=%u b0=%u a1=%u b1=%u v0=%u v1=%u delta=%u\n",
	       a0, b0, a1, b1, v0, v1, v1 - v0);
	zassert_true(v1 != v0, "counter did not progress");
	zassert_ok(counter_stop(rtc_counter), "stop counter");
}
ZTEST_SUITE(ref_counter_bracket, NULL, NULL, NULL, NULL, NULL);
