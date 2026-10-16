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

ZTEST(periodic_timer, test_expiry_and_stop)
{
	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(10), K_MSEC(10));

	for (int i = 0; i < 2; i++) {
		zassert_true(k_timer_status_sync(&periodic_timer) > 0,
			     "Expected a timer expiry");
	}
	zassert_true(atomic_get(&callback_count) >= 2,
		     "Expected at least two expiry callbacks");

	k_timer_stop(&periodic_timer);
	/* Discard any expiry that occurred between the last sync and stop. */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0,
		      "Stopped timer reported another expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
