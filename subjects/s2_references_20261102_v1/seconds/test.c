/* SPDX-License-Identifier: Apache-2.0 */
#include "../common.h"
#include <zephyr/drivers/counter.h>

static const struct device *const dev = DEVICE_DT_GET(DT_ALIAS(rtc_0));

ZTEST(ref_seconds, test_a_rate_contract)
{
	/* The original 1200-ms, one-to-two-tick property is retained verbatim in
	 * substance. Its failure must not be hidden by a relaxed progress oracle.
	 */
	uint32_t start, now;
	zassert_true(device_is_ready(dev), "counter unavailable");
	zassert_ok(counter_get_value(dev, &start), "initial counter read");
	k_msleep(1200);
	zassert_ok(counter_get_value(dev, &now), "final counter read");
	uint32_t elapsed = now - start;
	printk("REF_RATE ticks_in_1200_ms=%u\n", elapsed);
	zassert_true(elapsed >= 1, "original rate contract minimum");
	zassert_true(elapsed <= 2, "original rate contract maximum");
}
ZTEST(ref_seconds, test_b_legal_clock_progress)
{
	uint32_t start, now, previous = 0;
	zassert_ok(counter_get_value(dev, &start), "initial progress read");
	uint32_t began = k_uptime_get_32();
	for (;;) {
		zassert_ok(counter_get_value(dev, &now), "progress read");
		uint32_t delta = now - start;
		zassert_true(delta >= previous, "counter went backwards");
		zassert_true(ref_elapsed(began) <= REF_TEN_TICK_CEILING_MS, "progress reference ceiling");
		if (delta >= 10) {
			zassert_equal(delta, 10, "missed exact progress target");
			zassert_true(ref_elapsed(began) >= REF_TEN_TICK_EARLIEST_MS, "premature independent-time counter progress");
			break;
		}
		previous = delta;
		k_msleep(REF_POLL_MS);
	}
	printk("REF_EVENT seconds_progress elapsed_ms=%u\n", ref_elapsed(began));
}
ZTEST_SUITE(ref_seconds, NULL, NULL, NULL, NULL, NULL);
