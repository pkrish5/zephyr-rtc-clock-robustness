#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORK_DELAY K_MSEC(20)
#define TICK_TOLERANCE_MS 1

static struct k_work_delayable delayed_work;
static struct k_sem completion_sem;
static atomic_t handler_count;
static int64_t scheduled_at_ms;
static int64_t handler_at_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_at_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&completion_sem);
}

ZTEST(system_work_delayable, test_delayed_work_runs_once_after_delay)
{
	atomic_set(&handler_count, 0);
	handler_at_ms = -1;
	k_sem_reset(&completion_sem);
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	scheduled_at_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, WORK_DELAY), 1,
		      "delayed work was not scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");

	zassert_equal(k_sem_take(&completion_sem, K_SECONDS(1)), 0,
		      "timed out waiting for delayed work");
	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_at_ms - scheduled_at_ms >=
		     (int64_t)K_MSEC(20).ticks * 0 + 20 - TICK_TOLERANCE_MS,
		     "handler ran before the requested delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(system_work_delayable, NULL, NULL, NULL, NULL, NULL);
