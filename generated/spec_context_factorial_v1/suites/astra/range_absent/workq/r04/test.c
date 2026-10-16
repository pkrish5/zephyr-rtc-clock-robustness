#include <zephyr/kernel.h>
#include <zephyr/irq.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define DELAY_MS 50
#define COMPLETION_TIMEOUT K_SECONDS(2)

K_SEM_DEFINE(completed, 0, 2);
static atomic_t handler_calls;
static int64_t handler_time_ms;

static void work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_calls);
	k_sem_give(&completed);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, work_handler);

ZTEST(delayed_work_tests, test_timer_driven_system_work)
{
	int ret;
	bool pending;
	int64_t start_ms;
	unsigned int key;
	const int64_t tick_ms = (int64_t)k_ticks_to_ms_ceil64(1);

	/* On this single CPU, capture pending state before timer delivery. */
	key = irq_lock();
	start_ms = k_uptime_get();
	ret = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	pending = k_work_delayable_is_pending(&delayed_work);
	irq_unlock(key);

	zassert_equal(ret, 1, "Fresh delayed work was not scheduled");
	zassert_true(pending, "Work was not pending immediately after scheduling");
	zassert_equal(atomic_get(&handler_calls), 0,
		      "Handler ran before the test blocked");

	ret = k_sem_take(&completed, COMPLETION_TIMEOUT);
	zassert_equal(ret, 0, "Timed out waiting for the handler");
	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler did not execute exactly once");

	/*
	 * Uptime and timeouts have tick granularity. Allow one tick,
	 * rounded up to milliseconds, when comparing uptime timestamps.
	 */
	zassert_true(handler_time_ms - start_ms + tick_ms >= DELAY_MS,
		     "Handler was observed earlier than the allowed delay");

	/*
	 * The cooperative system workqueue (-3) finishes the handler before
	 * this cooperative test thread (-2) resumes on the single CPU.
	 */
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work remained pending after completion");

	/* Observe another delay interval to catch an unexpected repeat. */
	ret = k_sem_take(&completed, K_MSEC(DELAY_MS));
	zassert_equal(ret, -EAGAIN, "Unexpected additional completion");
	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work became pending again");
}

ZTEST_SUITE(delayed_work_tests, NULL, NULL, NULL, NULL, NULL);
