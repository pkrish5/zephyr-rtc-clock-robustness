#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer periodic_timer;
static atomic_t expiry_count;

static void timer_expiry(struct k_timer *timer)
{
	(void)timer;
	atomic_inc(&expiry_count);
}

ZTEST(periodic_timer_test, test_expiry_sync_and_stop)
{
	uint32_t first;
	uint32_t second;

	atomic_set(&expiry_count, 0);
	k_timer_init(&periodic_timer, timer_expiry, NULL);
	k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&periodic_timer);
	second = k_timer_status_sync(&periodic_timer);
	k_timer_stop(&periodic_timer);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	zassert_true(atomic_get(&expiry_count) >= 2,
		     "Expected at least two interrupt-driven expiry callbacks");

	/* Discard any expirations accumulated before the stop. */
	(void)k_timer_status_get(&periodic_timer);
	zassert_equal(k_timer_status_sync(&periodic_timer), 0U,
		      "Stopped timer synchronization must report no expiry");
}

ZTEST_SUITE(periodic_timer_test, NULL, NULL, NULL, NULL, NULL);
