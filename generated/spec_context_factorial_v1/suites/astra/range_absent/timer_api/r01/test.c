#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t expiry_count;

static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&expiry_count);
}

ZTEST(periodic_timer_test, test_expiry_status_sync)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t stopped_count;

	atomic_set(&expiry_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	k_timer_stop(&periodic_timer);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	stopped_count = atomic_get(&expiry_count);
	zassert_true(stopped_count >= 2, "Expiry callback ran fewer than twice");
	zassert_equal(k_timer_remaining_get(&periodic_timer), 0U,
		      "Stopped timer still has time remaining");

	/* Discard any expiry accumulated before stop while this thread waited. */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer reported an expiry");

	k_sleep(K_MSEC(60));
	zassert_equal(atomic_get(&expiry_count), stopped_count,
		      "Expiry callback ran after stop");
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer accumulated a new expiry");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
