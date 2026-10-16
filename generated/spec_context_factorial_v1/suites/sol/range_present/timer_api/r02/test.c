#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expired(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer, test_status_sync_and_stop)
{
	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expired, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	zassert_true(k_timer_status_sync(&periodic_timer) > 0,
		     "first expiration was not reported");
	zassert_true(k_timer_status_sync(&periodic_timer) > 0,
		     "second expiration was not reported");
	zassert_true(atomic_get(&callback_count) >= 2,
		     "expiry callback ran fewer than twice");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0,
		      "stopped timer reported an expiration");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
