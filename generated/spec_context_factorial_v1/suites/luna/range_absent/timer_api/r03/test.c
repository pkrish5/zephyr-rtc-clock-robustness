#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(timer_interrupt, test_periodic_timer_expirations_and_stop)
{
	callback_count = 0U;
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	uint32_t first = k_timer_status_sync(&periodic_timer);
	zassert_true(first > 0U, "first synchronization must report an expiry");
	uint32_t second = k_timer_status_sync(&periodic_timer);
	zassert_true(second > 0U, "second synchronization must report an expiry");
	zassert_true(callback_count >= 2U,
		     "expiry callback count should reflect periodic expirations");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "synchronization after stop must report no expiry");
}

static void *timer_suite_setup(void)
{
	k_timer_init(&periodic_timer, timer_expiry_fn, NULL);
	return NULL;
}

ZTEST_SUITE(timer_interrupt, NULL, timer_suite_setup, NULL, NULL, NULL);
