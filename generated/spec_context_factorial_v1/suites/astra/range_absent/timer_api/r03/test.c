#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer timer;
static atomic_t expiry_count;

static void timer_expiry(struct k_timer *expired_timer)
{
	ARG_UNUSED(expired_timer);
	atomic_inc(&expiry_count);
}

ZTEST(periodic_timer, test_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t callbacks;

	atomic_set(&expiry_count, 0);
	k_timer_init(&timer, timer_expiry, NULL);
	k_timer_start(&timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&timer);
	second = k_timer_status_sync(&timer);

	/* Stop before assertions so failures cannot leave the timer running. */
	k_timer_stop(&timer);
	callbacks = atomic_get(&expiry_count);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	zassert_true(callbacks >= 2, "Expiry callback ran fewer than twice");
	zassert_true((uint64_t)callbacks >= (uint64_t)first + second,
		     "Reported expirations exceed callback count");
	zassert_equal(k_timer_remaining_get(&timer), 0U,
		      "Stopped timer still has time remaining");

	/* Discard expirations that may have accumulated before the stop. */
	(void)k_timer_status_get(&timer);
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer synchronization reported an expiry");

	k_sleep(K_MSEC(60));
	zassert_equal(atomic_get(&expiry_count), callbacks,
		      "Expiry callback ran after the stop");
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer accumulated another expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
