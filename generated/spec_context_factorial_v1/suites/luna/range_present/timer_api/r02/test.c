#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t expiry_count;

static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&expiry_count);
}

ZTEST(timer_interrupt, test_periodic_expirations_and_stop)
{
	atomic_set(&expiry_count, 0);
	k_timer_init(&periodic_timer, timer_expiry_fn, NULL);
	k_timer_start(&periodic_timer, K_MSEC(50), K_MSEC(50));

	uint32_t first = k_timer_status_sync(&periodic_timer);
	uint32_t second = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0U, "first synchronization saw no expiry");
	zassert_true(second > 0U, "second synchronization saw no expiry");
	zassert_true(atomic_get(&expiry_count) >= 2,
		     "expiry callback count was %d", (int)atomic_get(&expiry_count));

	k_timer_stop(&periodic_timer);

	/* Consume any expiry that raced with stopping, then verify none remain. */
	(void)k_timer_status_sync(&periodic_timer);
	uint32_t after_stop = k_timer_status_sync(&periodic_timer);
	zassert_equal(after_stop, 0U, "stopped timer reported another expiry");
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
