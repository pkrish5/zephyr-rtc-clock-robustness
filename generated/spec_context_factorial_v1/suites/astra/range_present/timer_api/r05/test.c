#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;
static atomic_t wrong_context;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);

	if (!k_is_in_isr()) {
		atomic_set(&wrong_context, 1);
	}
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer_test, test_interrupt_expirations_and_stop)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t count_at_stop;

	atomic_clear(&callback_count);
	atomic_clear(&wrong_context);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	/* Synchronization consumes status, so these observe distinct expirations.
	 * No upper ISR-to-thread delivery-latency bound is assumed.
	 */
	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	k_timer_stop(&periodic_timer);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	count_at_stop = atomic_get(&callback_count);
	zassert_true(count_at_stop >= 2, "Expected at least two expiry callbacks");
	zassert_equal(atomic_get(&wrong_context), 0,
		      "Expiry callback did not run in interrupt context");

	/* Stop preserves unread status. Discard any expiry that occurred
	 * between the second synchronization and stopping the timer.
	 */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer synchronization reported an expiry");

	k_sleep(K_MSEC(40));
	zassert_equal(atomic_get(&callback_count), count_at_stop,
		      "Expiry callback ran after stop");
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer accumulated another expiry");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
