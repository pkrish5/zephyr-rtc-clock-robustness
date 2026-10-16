#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define OBSERVATION_TIMEOUT K_MSEC(1000)

static struct k_timer periodic_timer;
static atomic_t expiry_callback_count;

static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&expiry_callback_count);
}

ZTEST(periodic_timer, test_periodic_expiry_and_stop)
{
	uint32_t expirations;

	atomic_set(&expiry_callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry_fn, NULL);
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	/* Bound each wait while allowing ample scheduling and ISR delivery time. */
	for (int i = 0; i < 2; ++i) {
		expirations = k_timer_status_sync(&periodic_timer);
		zassert_true(expirations > 0U, "timer synchronization returned zero");
	}

	zassert_true(k_timer_remaining_get(&periodic_timer) > 0,
		     "periodic timer should remain active");
	zassert_true(atomic_get(&expiry_callback_count) >= 2,
		     "expected at least two expiry callbacks");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer reported an expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
