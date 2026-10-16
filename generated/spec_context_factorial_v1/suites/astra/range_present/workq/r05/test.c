#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/irq.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys_clock.h>

#define DELAY_MS 50

static K_SEM_DEFINE(completed, 0, 1);
static atomic_t handler_calls;
static int64_t handler_time_ms;
static struct k_work_sync work_sync;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_calls);
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work_test, test_timer_driven_execution)
{
	int rc;
	bool pending;
	int64_t scheduled_ms;
	atomic_val_t initial_calls;
	const int64_t tick_ms = (int64_t)k_ticks_to_ms_ceil64(1);
	const int64_t minimum_ms = DELAY_MS > tick_ms ?
		DELAY_MS - tick_ms : 0;

	/* On this single CPU, exclude timer delivery while taking the
	 * immediate scheduling observations. Assert only after unlocking.
	 */
	unsigned int key = irq_lock();

	scheduled_ms = k_uptime_get();
	rc = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	pending = k_work_delayable_is_pending(&delayed_work);
	initial_calls = atomic_get(&handler_calls);
	irq_unlock(key);

	zassert_equal(rc, 1, "Fresh delayed work was not scheduled");
	zassert_true(pending, "Work was not pending immediately after scheduling");
	zassert_equal(initial_calls, 0, "Handler ran before initial observations");

	/* Clock accuracy alone provides no delivery-latency upper bound.
	 * Wait for actual completion instead of assuming a fixed sleep suffices.
	 */
	rc = k_sem_take(&completed, K_FOREVER);
	zassert_equal(rc, 0, "Completion wait failed");

	/* The semaphore is signaled inside the handler; flushing additionally
	 * ensures that the handler has returned and work bookkeeping is done.
	 */
	(void)k_work_flush_delayable(&delayed_work, &work_sync);

	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler must execute exactly once");

	/* Measure kernel time, not independently calibrated wall time.
	 * Allow one tick (rounded up to milliseconds) for tick granularity
	 * and the millisecond representation of uptime.
	 */
	zassert_true(handler_time_ms - scheduled_ms >= minimum_ms,
		     "Handler was observed before the permitted delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work remains pending after completion");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
