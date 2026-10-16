#include <zephyr/kernel.h>
#include <zephyr/irq.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define DELAY_MS 50

K_SEM_DEFINE(completed, 0, 1);
static atomic_t executions;
static int64_t handler_time_ms;

static void work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&executions);
	k_sem_give(&completed);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, work_handler);

ZTEST(delayed_work_test, test_timer_delivery)
{
	struct k_work_sync sync;
	int64_t scheduled_at_ms;
	bool initially_pending;
	int schedule_result;
	unsigned int key;

	atomic_set(&executions, 0);
	k_sem_reset(&completed);

	/* Prevent timeout delivery between scheduling and the pending check. */
	key = irq_lock();
	scheduled_at_ms = k_uptime_get();
	schedule_result = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	initially_pending = k_work_delayable_is_pending(&delayed_work);
	irq_unlock(key);

	zassert_equal(schedule_result, 1, "Fresh work was not scheduled");
	zassert_true(initially_pending, "Scheduled work was not pending");

	/* A generous liveness watchdog, not a claimed delivery-latency bound. */
	zassert_equal(k_sem_take(&completed, K_SECONDS(5)), 0,
		      "Handler did not signal completion");
	/* The semaphore signals inside the handler; flush joins its return. */
	(void)k_work_flush_delayable(&delayed_work, &sync);

	zassert_equal(atomic_get(&executions), 1,
		      "Handler did not execute exactly once");

	/*
	 * Use the same kernel clock for scheduling and observation. Allow one
	 * tick of granularity plus one millisecond for uptime quantization.
	 * HSI accuracy does not establish an ISR-to-thread latency bound.
	 */
	const int64_t tolerance_ms =
		(int64_t)k_ticks_to_ms_ceil64(1) + 1;

	zassert_true(handler_time_ms - scheduled_at_ms + tolerance_ms >= DELAY_MS,
		     "Handler was observed too early");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work is still pending");

	/* Observe a further interval to catch an unintended repeat. */
	k_sleep(K_MSEC(2 * DELAY_MS));
	zassert_equal(atomic_get(&executions), 1, "Handler executed again");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
