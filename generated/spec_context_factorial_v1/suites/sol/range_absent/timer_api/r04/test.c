#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

static struct k_timer periodic_timer;
static atomic_t expiry_callbacks;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&expiry_callbacks);
}

ZTEST(timer_sync, test_periodic_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;

	atomic_set(&expiry_callbacks, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(50), K_MSEC(50));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);

	k_timer_stop(&periodic_timer);

	zassert_true(first > 0U, "first synchronization reported no expiry");
	zassert_true(second > 0U, "second synchronization reported no expiry");
	zassert_true(atomic_get(&expiry_callbacks) >= 2,
		     "expiry callback ran fewer than twice");
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer reported an expiry");
}

ZTEST_SUITE(timer_sync, NULL, NULL, NULL, NULL, NULL);
