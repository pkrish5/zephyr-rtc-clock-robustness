#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer_api, test_status_sync_and_stop)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t count_at_stop;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(10), K_MSEC(10));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	zassert_true(first > 0U, "first synchronization reported no expiry");
	zassert_true(second > 0U, "second synchronization reported no expiry");
	zassert_true(atomic_get(&callback_count) >= 2,
		     "expiry callback ran fewer than twice");

	k_timer_stop(&periodic_timer);
	count_at_stop = atomic_get(&callback_count);
	(void)k_timer_status_get(&periodic_timer);
	k_sleep(K_MSEC(25));
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "synchronization reported an expiry after stop");
	zassert_equal(atomic_get(&callback_count), count_at_stop,
		      "expiry callback ran after stop");
}

ZTEST_SUITE(periodic_timer_api, NULL, NULL, NULL, NULL, NULL);
