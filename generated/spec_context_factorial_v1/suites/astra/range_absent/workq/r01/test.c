#include <zephyr/kernel.h>
#include <zephyr/irq.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define DELAY_MS 50

static K_SEM_DEFINE(completed, 0, 2);
static atomic_t executions;
static int64_t handler_time_ms;

static void work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&executions);
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, work_handler);

ZTEST(delayed_work_test, test_timer_driven_work)
{
	int result;
	bool pending;
	int64_t start_ms;
	unsigned int key;
	const int64_t tick_ms = k_ticks_to_ms_ceil64(1);

	atomic_clear(&executions);
	k_sem_reset(&completed);

	/* Prevent timer expiry between scheduling and the pending snapshot. */
	key = irq_lock();
	start_ms = k_uptime_get();
	result = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	pending = k_work_delayable_is_pending(&delayed_work);
	irq_unlock(key);

	zassert_equal(result, 1, "Fresh work was not scheduled");
	zassert_true(pending, "Scheduled work was not pending");

	zassert_equal(k_sem_take(&completed, K_MSEC(1000)), 0,
		      "Handler did not complete");
	zassert_equal(atomic_get(&executions), 1,
		      "Handler must execute exactly once");

	/* Allow one tick for timeout phase and uptime millisecond rounding. */
	zassert_true(handler_time_ms - start_ms + tick_ms >= DELAY_MS,
		     "Handler ran before the requested delay");

	/* The higher-priority cooperative system worker finishes before us. */
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work is still pending");

	/* Observe another two delay periods to catch unintended repetition. */
	k_sleep(K_MSEC(2 * DELAY_MS));
	zassert_equal(atomic_get(&executions), 1,
		      "Handler executed again");
	zassert_true(k_sem_take(&completed, K_NO_WAIT) != 0,
		     "Unexpected additional completion");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
