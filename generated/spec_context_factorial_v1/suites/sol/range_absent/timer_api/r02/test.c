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

ZTEST(timer_periodic, test_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0, "first synchronization reported no expiry");
	zassert_true(second > 0, "second synchronization reported no expiry");
	zassert_true(atomic_get(&callback_count) >= 2,
		     "expiry callback ran fewer than twice");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0,
		      "synchronization reported an expiry after stop");
}

ZTEST_SUITE(timer_periodic, NULL, NULL, NULL, NULL, NULL);
