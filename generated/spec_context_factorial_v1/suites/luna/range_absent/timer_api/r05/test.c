#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define TIMER_TIMEOUT K_MSEC(1000)

static struct k_timer periodic_timer;
static uint32_t callback_count;

static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	callback_count++;
}

ZTEST(timer_expiry, test_periodic_timer_expirations)
{
	uint32_t expirations;

	callback_count = 0U;
	k_timer_init(&periodic_timer, timer_expiry_fn, NULL);
	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	expirations = k_timer_status_sync(&periodic_timer);
	zassert_true(expirations > 0U, "first synchronization should report expiry");

	expirations = k_timer_status_sync(&periodic_timer);
	zassert_true(expirations > 0U, "second synchronization should report expiry");
	zassert_true(callback_count >= 2U, "expiry callback count was %u", callback_count);

	k_timer_stop(&periodic_timer);
	expirations = k_timer_status_sync(&periodic_timer);
	zassert_equal(expirations, 0U, "stopped timer should report no pending expiry");
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
