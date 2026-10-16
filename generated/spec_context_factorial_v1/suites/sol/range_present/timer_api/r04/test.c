#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	(void)timer;
	atomic_inc(&callback_count);
}

ZTEST(timer_interrupt_path, test_periodic_expiry_and_stop)
{
	unsigned int first;
	unsigned int second;
	unsigned int after_stop;
	atomic_val_t callbacks;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	callbacks = atomic_get(&callback_count);

	k_timer_stop(&periodic_timer);
	after_stop = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0U, "first synchronization missed expiry");
	zassert_true(second > 0U, "second synchronization missed expiry");
	zassert_true(callbacks >= 2, "expiry callback ran fewer than twice");
	zassert_equal(after_stop, 0U, "synchronization reported expiry after stop");
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
