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

ZTEST(periodic_timer_test, test_expiry_and_stop)
{
	uint32_t first, second;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(25), K_MSEC(25));

	first = k_timer_status_sync(&periodic_timer);
	zassert_true(first > 0, "first synchronization saw no expiry");

	second = k_timer_status_sync(&periodic_timer);
	zassert_true(second > 0, "second synchronization saw no expiry");
	zassert_true(atomic_get(&callback_count) >= first + second,
		     "expiry callback count is too small");

	k_timer_stop(&periodic_timer);
	/* Discard any expiry recorded between the second sync and stop. */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0,
		      "stopped timer reported an expiry");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
