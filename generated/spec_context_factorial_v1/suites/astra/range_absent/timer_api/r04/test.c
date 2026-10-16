#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;
static atomic_t interrupt_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&callback_count);
	if (k_is_in_isr()) {
		atomic_inc(&interrupt_count);
	}
}

ZTEST(periodic_timer_test, test_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t callbacks;

	atomic_set(&callback_count, 0);
	atomic_set(&interrupt_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	k_timer_stop(&periodic_timer);

	zassert_true(first > 0U, "First synchronization missed expiry");
	zassert_true(second > 0U, "Second synchronization missed expiry");

	callbacks = atomic_get(&callback_count);
	zassert_true(callbacks >= 2, "Expected at least two callbacks");
	zassert_equal(atomic_get(&interrupt_count), callbacks,
		      "Expiry callbacks must run in interrupt context");

	/* Discard any expirations queued before the timer was stopped. */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer must return zero without waiting");

	k_sleep(K_MSEC(60));
	zassert_equal(atomic_get(&callback_count), callbacks,
		      "Callback occurred after stopping");
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer reported another expiry");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
