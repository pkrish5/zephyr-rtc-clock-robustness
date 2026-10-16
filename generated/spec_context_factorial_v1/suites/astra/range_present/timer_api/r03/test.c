#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t callback_count;

static void timer_expired(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	/* The kernel invokes this callback from the timer interrupt path. */
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer_tests, test_expiry_status_sync)
{
	uint32_t first_status;
	uint32_t second_status;
	atomic_val_t observed_callbacks;

	atomic_set(&callback_count, 0);
	k_timer_init(&periodic_timer, timer_expired, NULL);
	k_timer_start(&periodic_timer, K_MSEC(10), K_MSEC(10));

	first_status = k_timer_status_sync(&periodic_timer);
	second_status = k_timer_status_sync(&periodic_timer);
	observed_callbacks = atomic_get(&callback_count);

	k_timer_stop(&periodic_timer);

	/*
	 * Stop preserves accumulated status. Drain any expiry that raced
	 * with stopping before checking for further notifications.
	 */
	(void)k_timer_status_get(&periodic_timer);

	zassert_true(first_status > 0, "First synchronization missed expiry");
	zassert_true(second_status > 0, "Second synchronization missed expiry");
	zassert_true(observed_callbacks >= 2, "Expected at least two callbacks");
	zassert_equal(k_timer_status_sync(&periodic_timer), 0,
		      "Stopped timer reported another expiry");
}

ZTEST_SUITE(periodic_timer_tests, NULL, NULL, NULL, NULL, NULL);
