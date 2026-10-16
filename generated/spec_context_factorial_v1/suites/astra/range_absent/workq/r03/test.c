#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

#define DELAY_MS 60

static K_SEM_DEFINE(completed, 0, 2);
static atomic_t executions;
static int64_t handler_time_ms;

static void work_handler(struct k_work *work)
{
	ARG_UNUSED(work);

	if (atomic_inc(&executions) == 0) {
		handler_time_ms = k_uptime_get();
	}
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, work_handler);

ZTEST(delayed_work_test, test_delayed_system_work)
{
	const int64_t tick_ms = k_ticks_to_ms_ceil64(1);
	int64_t start_ms;
	int64_t elapsed_ms;
	int rc;

	start_ms = k_uptime_get();
	rc = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	zassert_equal(rc, 1, "Fresh delayed work was not scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "Scheduled work must be pending");
	zassert_equal(atomic_get(&executions), 0,
		      "Handler ran before the initial pending check");
	zassert_true(k_uptime_get() - start_ms < DELAY_MS,
		     "Initial pending check missed the delay window");

	rc = k_sem_take(&completed, K_SECONDS(2));
	zassert_equal(rc, 0, "Timed out waiting for the handler");
	zassert_equal(atomic_get(&executions), 1,
		      "Handler must execute exactly once");

	/* Allow one tick for timeout/uptime quantization. */
	elapsed_ms = handler_time_ms - start_ms;
	zassert_true(elapsed_ms + tick_ms >= DELAY_MS,
		     "Handler executed before the requested delay");

	/*
	 * With the supplied cooperative priorities on this single CPU,
	 * the system workqueue finishes the handler and clears its running
	 * state before this awakened test thread can resume.
	 */
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work must no longer be pending");

	zassert_equal(k_sem_take(&completed, K_MSEC(DELAY_MS)), -EAGAIN,
		      "Unexpected additional handler completion");
	zassert_equal(atomic_get(&executions), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work unexpectedly became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
