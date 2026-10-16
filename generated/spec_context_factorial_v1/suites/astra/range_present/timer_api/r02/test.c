#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer timer;
static atomic_t expiry_count;
static atomic_t non_isr_expiry;

static void timer_expiry(struct k_timer *expired)
{
	ARG_UNUSED(expired);
	if (!k_is_in_isr()) {
		atomic_set(&non_isr_expiry, 1);
	}
	atomic_inc(&expiry_count);
}

ZTEST(periodic_timer, test_interrupt_expirations)
{
	uint32_t first;
	uint32_t second;
	uint32_t stopped_status;
	atomic_val_t observed;

	atomic_set(&expiry_count, 0);
	atomic_set(&non_isr_expiry, 0);
	k_timer_init(&timer, timer_expiry, NULL);
	k_timer_start(&timer, K_MSEC(20), K_MSEC(20));

	/* Block in thread context for two successive status observations.
	 * Counts may exceed one: no ISR-to-thread latency bound is assumed.
	 */
	first = k_timer_status_sync(&timer);
	second = k_timer_status_sync(&timer);
	k_timer_stop(&timer);

	observed = atomic_get(&expiry_count);
	/* Discard expirations that occurred between the last sync and stop.
	 * Stopping does not clear already accumulated expiration status.
	 */
	(void)k_timer_status_get(&timer);
	stopped_status = k_timer_status_sync(&timer);

	zassert_true(first > 0U, "First synchronization missed expiry");
	zassert_true(second > 0U, "Second synchronization missed expiry");
	zassert_true(observed >= 2, "Expected at least two expiry callbacks");
	zassert_equal(atomic_get(&non_isr_expiry), 0,
		      "Expiry callback ran outside interrupt context");
	zassert_equal(k_timer_remaining_get(&timer), 0U,
		      "Stopped timer still has time remaining");
	zassert_equal(stopped_status, 0U,
		      "Stopped timer reported a new expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
