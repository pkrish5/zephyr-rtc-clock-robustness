#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORK_DELAY K_MSEC(20)
#define WORK_DELAY_MS 20

static struct k_work_delayable delayed_work;
static struct k_sem work_done;
static atomic_t handler_count;
static int64_t handler_time_ms;
static int64_t scheduled_time_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST(system_workqueue_delayable, test_delayed_work_runs_once_after_delay)
{
	k_sem_init(&work_done, 0, 1);
	atomic_set(&handler_count, 0);
	handler_time_ms = -1;
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	scheduled_time_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, WORK_DELAY), 1,
		      "work should be scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending after scheduling");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "delayed work handler did not run");

	/* Allow one system tick of granularity when comparing millisecond time. */
	zassert_true(handler_time_ms - scheduled_time_ms >= WORK_DELAY_MS - 1,
		     "handler ran before the requested delay");
	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should not be pending after completion");
}

ZTEST_SUITE(system_workqueue_delayable, NULL, NULL, NULL, NULL, NULL);
