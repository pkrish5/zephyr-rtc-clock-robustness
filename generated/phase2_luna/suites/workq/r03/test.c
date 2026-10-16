#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TEST_DELAY K_MSEC(100)
#define TICK_TOLERANCE_MS 1

K_SEM_DEFINE(work_done, 0, 1);
K_WORK_DELAYABLE_DEFINE(delayed_work, NULL);

static atomic_t handler_calls;
static int64_t handler_time_ms;
static int64_t scheduled_time_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_calls);
	k_sem_give(&work_done);
}

ZTEST(delayable_work, test_system_workqueue_delayed_execution)
{
	struct k_work_delayable *dwork = &delayed_work;
	int ret;

	atomic_set(&handler_calls, 0);
	handler_time_ms = 0;
	(void)k_sem_reset(&work_done);
	k_work_init_delayable(dwork, delayed_work_handler);

	scheduled_time_ms = k_uptime_get();
	ret = k_work_schedule(dwork, TEST_DELAY);
	zassert_true(ret >= 0, "Scheduling delayed work failed: %d", ret);
	zassert_true(k_work_delayable_is_pending(dwork),
		     "Delayed work is not pending immediately after scheduling");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "Timed out waiting for delayed work handler");

	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler ran %d times", atomic_get(&handler_calls));
	zassert_true(handler_time_ms - scheduled_time_ms >=
		     100 - TICK_TOLERANCE_MS,
		     "Handler ran too early: elapsed %lld ms",
		     (long long)(handler_time_ms - scheduled_time_ms));
	zassert_false(k_work_delayable_is_pending(dwork),
		      "Delayed work is still pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
