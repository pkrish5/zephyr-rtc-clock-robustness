/* SPDX-License-Identifier: Apache-2.0 */
#ifndef COUNTER_VERIFY_COMMON_H
#define COUNTER_VERIFY_COMMON_H
#include <zephyr/device.h>
#include <zephyr/drivers/counter.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>

/* Preregistered experimental allowances, not physical service guarantees. */
#define VERIFY_ONE_CEILING_MS 11000U
#define VERIFY_TWO_CEILING_MS 13000U
#define VERIFY_ONE_EARLIEST_MS 678U
#define VERIFY_TWO_EARLIEST_MS 1360U
#define VERIFY_POLL_MS 20U

static const struct device *const verify_dev = DEVICE_DT_GET(DT_ALIAS(rtc_0));
static inline uint32_t elapsed_ms(uint32_t start)
{
	return k_uptime_get_32() - start;
}
static inline void require_counter(void)
{
	zassert_true(device_is_ready(verify_dev), "RTC-only counter unavailable");
	zassert_equal(counter_get_num_of_channels(verify_dev), 1, "channel capability changed");
	zassert_equal(counter_get_frequency(verify_dev), 1, "nominal divider policy changed");
}
#endif
