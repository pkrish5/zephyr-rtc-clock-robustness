#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expiry_handler(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&callback_count);
}

ZTEST(timer_expiry, test_periodic_expirations_and_stop)
{
	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry_handler, NULL);
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	uint32_t first = k_timer_status_sync(&periodic_timer);
	uint32_t second = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0U, "first timer synchronization reported no expiry");
	zassert_true(second > 0U, "second timer synchronization reported no expiry");
	zassert_true(atomic_get(&callback_count) >= 2,
		     "expiry callback count was %d", atomic_get(&callback_count));

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer reported an expiry");
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
