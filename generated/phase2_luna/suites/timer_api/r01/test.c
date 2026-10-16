#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define EXPIRY_CHECK_TIMEOUT K_MSEC(1000)

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(timer_interrupt, test_periodic_timer_expirations_and_stop)
{
	callback_count = 0U;
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	uint32_t first_status = k_timer_status_sync(&periodic_timer);
	zassert_true(first_status > 0U, "first timer synchronization should report expiry");

	uint32_t second_status = k_timer_status_sync(&periodic_timer);
	zassert_true(second_status > 0U, "second timer synchronization should report expiry");
	zassert_true(callback_count >= 2U,
		     "expiry callback count should reflect at least two expirations");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "stopped timer should report no further expirations");
}

static void *timer_test_setup(void)
{
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	return NULL;
}

ZTEST_SUITE(timer_interrupt, NULL, timer_test_setup, NULL, NULL, NULL);
