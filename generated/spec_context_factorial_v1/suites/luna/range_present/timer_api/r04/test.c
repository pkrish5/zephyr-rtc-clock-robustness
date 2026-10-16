#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define EXPIRATION_LIMIT 4

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry_handler(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(timer_periodic, test_periodic_expirations_and_stop)
{
	uint32_t first_count;
	uint32_t second_count;

	callback_count = 0U;
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	first_count = k_timer_status_sync(&periodic_timer);
	zassert_true(first_count > 0U, "first synchronization must report an expiry");
	second_count = k_timer_status_sync(&periodic_timer);
	zassert_true(second_count > 0U, "second synchronization must report an expiry");
	zassert_true(callback_count >= 2U, "expiry callback should have run at least twice");
	zassert_true(k_timer_remaining_get(&periodic_timer) > 0,
		     "periodic timer should remain active before stopping");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer should have no pending expiry");
}

static void *timer_suite_setup(void)
{
	k_timer_init(&periodic_timer, timer_expiry_handler, NULL);
	return NULL;
}

ZTEST_SUITE(timer_periodic, NULL, timer_suite_setup, NULL, NULL, NULL);
