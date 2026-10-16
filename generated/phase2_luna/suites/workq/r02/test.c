#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORK_DELAY K_MSEC(20)
#define TICK_TOLERANCE_MS 1

static struct k_work_delayable delayed_work;
static struct k_sem work_done;
static atomic_t handler_count;
static int64_t schedule_time_ms;
static int64_t handler_time_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST(delayable_work, test_system_workqueue_delay_and_completion)
{
	k_sem_reset(&work_done);
	atomic_set(&handler_count, 0);
	handler_time_ms = 0;
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	schedule_time_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, WORK_DELAY), 1,
		      "work should be newly scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending before its delay elapses");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "timed out waiting for delayed work");
	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_time_ms - schedule_time_ms >=
		     (int64_t)K_MSEC(20).ticks * 0 + 20 - TICK_TOLERANCE_MS,
		     "handler ran earlier than the requested delay, allowing tick granularity");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
