/* SPDX-License-Identifier: Apache-2.0 */
#include "common.h"

ZTEST(ref_counter_progress, test_progress)
{
	uint32_t first, now, delta, began;
	require_counter();
	zassert_ok(counter_cancel_channel_alarm(verify_dev, 0), "clear callback state");
	zassert_ok(counter_stop(verify_dev), "clean stop");
	zassert_ok(counter_start(verify_dev), "start progress control");
	began = k_uptime_get_32();
	zassert_ok(counter_get_value(verify_dev, &first), "initial counter read");
	for (;;) {
		zassert_ok(counter_get_value(verify_dev, &now), "progress counter read");
		delta = now - first;
		zassert_true(elapsed_ms(began) <= 20000U, "five-tick progress ceiling");
		if (delta >= 5U) { break; }
		k_msleep(VERIFY_POLL_MS);
	}
	printk("VERIFY_RATE delta_ticks=%u elapsed_ms=%u\n", delta, elapsed_ms(began));
	zassert_ok(counter_stop(verify_dev), "stop progress control");
}
ZTEST_SUITE(ref_counter_progress, NULL, NULL, NULL, NULL, NULL);
