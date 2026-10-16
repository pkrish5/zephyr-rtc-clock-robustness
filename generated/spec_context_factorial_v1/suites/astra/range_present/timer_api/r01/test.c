#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer_test, test_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;
	uint32_t stopped_status;
	atomic_val_t callbacks;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(10), K_MSEC(10));

	/* Observe two successive batches of interrupt-driven expirations. */
	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);

	k_timer_stop(&periodic_timer);
	callbacks = atomic_get(&callback_count);

	/* Stop preserves status: consume expirations pending before the stop. */
	(void)k_timer_status_get(&periodic_timer);
	stopped_status = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	zassert_true(callbacks >= 2, "Expected at least two expiry callbacks");
	zassert_equal(stopped_status, 0U,
		      "Stopped timer synchronization reported an expiry");
	zassert_equal(atomic_get(&callback_count), callbacks,
		      "Expiry callback ran after stopping");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
