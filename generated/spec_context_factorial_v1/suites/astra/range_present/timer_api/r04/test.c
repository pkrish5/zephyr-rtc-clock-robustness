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

ZTEST(periodic_timer, test_interrupt_expiry_and_stop)
{
	uint32_t first;
	uint32_t second;
	atomic_val_t stopped_count;

	atomic_set(&callback_count, 0);
	atomic_set(&non_isr_callback, 0);
	k_timer_init(&timer, timer_expiry, NULL);
	k_timer_start(&timer, K_MSEC(20), K_MSEC(20));

	/* Each synchronization consumes the accumulated expiration count. */
	first = k_timer_status_sync(&timer);
	second = k_timer_status_sync(&timer);
	k_timer_stop(&timer);

	zassert_true(first > 0U, "First synchronization missed expiry");
	zassert_true(second > 0U, "Second synchronization missed expiry");
	stopped_count = atomic_get(&callback_count);
	zassert_true(stopped_count >= 2, "Expected at least two callbacks");
	zassert_equal(atomic_get(&non_isr_callback), 0,
		      "Expiry callback ran outside interrupt context");

	/* Stop preserves any status accumulated before it took effect.
	 * Consume that backlog before checking for further expirations.
	 */
	(void)k_timer_status_get(&timer);
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer reported another expiry");

	/* Allow multiple former periods to pass; impose no delivery deadline. */
	k_sleep(K_MSEC(60));
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "Stopped timer accumulated new expirations");
	zassert_equal(atomic_get(&callback_count), stopped_count,
		      "Callback ran after timer was stopped");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
