#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static struct k_timer timer;
static atomic_t callback_count;
static atomic_t non_isr_callback;

static void timer_expiry(struct k_timer *expired_timer)
{
	ARG_UNUSED(expired_timer);
	if (!k_is_in_isr()) {
		atomic_set(&non_isr_callback, 1);
	}
	atomic_inc(&callback_count);
}

ZTEST(periodic_timer, test_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;
	uint32_t total;

	atomic_clear(&callback_count);
	atomic_clear(&non_isr_callback);
	k_timer_init(&timer, timer_expiry, NULL);
	k_timer_start(&timer, K_MSEC(20), K_MSEC(20));

	first = k_timer_status_sync(&timer);
	second = k_timer_status_sync(&timer);
	k_timer_stop(&timer);

	/* Include any expirations pending between the last sync and stop. */
	total = first + second + k_timer_status_get(&timer);

	zassert_true(first > 0U, "First synchronization reported no expiry");
	zassert_true(second > 0U, "Second synchronization reported no expiry");
	zassert_true(atomic_get(&callback_count) >= 2,
		     "Expected at least two expiry callbacks");
	zassert_equal((uint32_t)atomic_get(&callback_count), total,
		      "Callback and expiration counts differ");
	zassert_equal(atomic_get(&non_isr_callback), 0,
		      "Expiry callback did not run in interrupt context");

	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer reported an expiry");
	k_sleep(K_MSEC(40));
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer reported a later expiry");
	zassert_equal((uint32_t)atomic_get(&callback_count), total,
		      "Expiry callback ran after stop");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
