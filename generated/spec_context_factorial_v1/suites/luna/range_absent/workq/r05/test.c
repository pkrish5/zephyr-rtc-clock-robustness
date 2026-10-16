#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define DELAY_MS 100
#define TICK_TOLERANCE_MS 1

static struct k_work_delayable delayed_work;
static struct k_sem work_done;
static atomic_t handler_count;
static int64_t scheduled_at_ms;
static int64_t handler_at_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_at_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST(system_work_delayable, test_delayed_work_runs_once_after_delay)
{
	k_sem_reset(&work_done);
	atomic_set(&handler_count, 0);
	handler_at_ms = 0;
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	scheduled_at_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, K_MSEC(DELAY_MS)), 1,
		      "work was not scheduled");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "timed out waiting for delayed work");

	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_at_ms - scheduled_at_ms >=
		     DELAY_MS - TICK_TOLERANCE_MS,
		     "handler ran before the requested delay, accounting for tick granularity");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(system_work_delayable, NULL, NULL, NULL, NULL, NULL);
