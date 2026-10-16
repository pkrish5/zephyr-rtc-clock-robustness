#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

static K_SEM_DEFINE(completed, 0, 2);
static atomic_t executions;
static int64_t handler_ms;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_ms = k_uptime_get();
	atomic_inc(&executions);
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work_test, test_timer_driven_execution)
{
	/* Allow one tick of timeout granularity and uptime's millisecond rounding. */
	const int64_t tolerance_ms = k_ticks_to_ms_ceil64(1) + 1;
	const int64_t delay_ms = 50 + 2 * tolerance_ms;
	struct k_work_sync sync;
	int64_t start_ms;
	int64_t pending_ms;
	bool pending;
	int scheduled;
	unsigned int key;

	atomic_set(&executions, 0);
	k_sem_reset(&completed);

	/* Keep scheduling and the initial observation ahead of timer delivery. */
	key = irq_lock();
	start_ms = k_uptime_get();
	scheduled = k_work_schedule(&delayed_work, K_MSEC(delay_ms));
	pending = k_work_delayable_is_pending(&delayed_work);
	pending_ms = k_uptime_get();
	irq_unlock(key);

	zassert_equal(scheduled, 1, "Fresh delayed work was not scheduled");
	zassert_true(pending, "Scheduled work was not pending");
	zassert_true(pending_ms - start_ms < delay_ms,
		     "Initial pending observation missed the delay window");

	/*
	 * This timeout is a practical liveness budget, not a delivery-latency
	 * bound inferred from the HSI's frequency accuracy. Both timestamps
	 * use Zephyr uptime; no external wall-clock accuracy is asserted.
	 */
	zassert_ok(k_sem_take(&completed, K_SECONDS(5)),
		   "Delayed handler did not signal completion");

	/* The signal precedes handler return; synchronize with full completion. */
	(void)k_work_flush_delayable(&delayed_work, &sync);

	zassert_equal(atomic_get(&executions), 1,
		      "Handler did not execute exactly once");
	zassert_true(handler_ms - start_ms >= delay_ms - tolerance_ms,
		     "Handler executed before the permitted delay boundary");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work is still pending");

	/* Observe an additional delay window for an unexpected repeat. */
	zassert_equal(k_sem_take(&completed, K_MSEC(delay_ms)), -EAGAIN,
		      "Handler unexpectedly signaled again");
	zassert_equal(atomic_get(&executions), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work unexpectedly became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
