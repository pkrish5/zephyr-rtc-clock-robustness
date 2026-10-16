#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define WAIT_TIMEOUT K_SECONDS(2)

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(periodic_timer, test_periodic_expirations_and_stop)
{
	uint32_t first_count;
	uint32_t second_count;

	callback_count = 0U;
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	first_count = k_timer_status_sync(&periodic_timer);
	zassert_true(first_count > 0U, "first timer synchronization must report an expiry");

	second_count = k_timer_status_sync(&periodic_timer);
	zassert_true(second_count > 0U, "second timer synchronization must report an expiry");
	zassert_true(callback_count >= 2U, "expiry callback count: %u", callback_count);
	zassert_true(k_timer_remaining_get(&periodic_timer) > 0,
		     "periodic timer should remain armed before stop");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer must not report a further expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
