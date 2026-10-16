#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define DELAY_MS 100
#define WAIT_TIMEOUT_MS 2000

K_SEM_DEFINE(work_done, 0, 1);
K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_work_handler);

static atomic_t handler_count;
static int64_t handler_time_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST(delayable_work, test_system_workqueue_delay)
{
	const int64_t scheduled_at_ms = k_uptime_get();
	const int64_t minimum_elapsed_ms = DELAY_MS - 1;

	atomic_set(&handler_count, 0);
	k_sem_reset(&work_done);
	zassert_equal(k_work_schedule(&delayed_work, K_MSEC(DELAY_MS)), 1,
		      "work should be scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");

	zassert_ok(k_sem_take(&work_done, K_MSEC(WAIT_TIMEOUT_MS)),
		   "work handler did not run before timeout");

	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_time_ms - scheduled_at_ms >= minimum_elapsed_ms,
		     "handler ran before delay, allowing one tick of granularity");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
