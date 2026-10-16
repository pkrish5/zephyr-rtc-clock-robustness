#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(periodic_timer, test_periodic_expiry_and_stop)
{
	callback_count = 0U;
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	uint32_t first_status = k_timer_status_sync(&periodic_timer);
	zassert_true(first_status > 0U, "first timer expiration was not reported");

	uint32_t second_status = k_timer_status_sync(&periodic_timer);
	zassert_true(second_status > 0U, "second timer expiration was not reported");
	zassert_true(callback_count >= 2U,
		     "expected at least two expiry callbacks, got %u", callback_count);
	zassert_true(k_timer_remaining_get(&periodic_timer) > 0,
		     "periodic timer should remain active");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer reported another expiration");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
