#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

#define WORK_DELAY_MS 100

static struct k_sem work_done;
static atomic_t handler_count;
static int64_t schedule_ticks;
static int64_t handler_ticks;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_ticks = k_uptime_ticks();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayable_work, test_system_workqueue_delay)
{
	int ret;

	k_sem_init(&work_done, 0, 1);
	atomic_set(&handler_count, 0);
	schedule_ticks = k_uptime_ticks();

	ret = k_work_schedule(&delayed_work, K_MSEC(WORK_DELAY_MS));
	zassert_true(ret >= 0, "k_work_schedule failed: %d", ret);
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending after scheduling");

	zassert_ok(k_sem_take(&work_done, K_SECONDS(2)),
		   "delayed work handler did not run");

	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_ticks - schedule_ticks >=
		     k_ms_to_ticks_ceil32(WORK_DELAY_MS),
		     "handler ran before the requested delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
