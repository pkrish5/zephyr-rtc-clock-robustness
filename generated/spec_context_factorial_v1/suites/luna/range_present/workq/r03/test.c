#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define DELAY_MS 50
#define TICK_ALLOWANCE_MS 1

K_SEM_DEFINE(work_done, 0, 1);
K_WORK_DELAYABLE_DEFINE(delayed_work, NULL);

static atomic_t handler_count;
static atomic_t handler_ran_early;
static int64_t scheduled_at_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);

	if ((k_uptime_get() - scheduled_at_ms) < (DELAY_MS - TICK_ALLOWANCE_MS)) {
		atomic_set(&handler_ran_early, 1);
	}
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST_SUITE(system_delayed_work, NULL, NULL, NULL, NULL, NULL);

ZTEST(system_delayed_work, test_timer_driven_delayed_work)
{
	struct k_work_delayable work;

	k_work_init_delayable(&work, delayed_work_handler);
	atomic_set(&handler_count, 0);
	atomic_set(&handler_ran_early, 0);
	k_sem_reset(&work_done);
	scheduled_at_ms = k_uptime_get();

	zassert_equal(k_work_schedule(&work, K_MSEC(DELAY_MS)), 1,
		      "delayed work should be newly scheduled");
	zassert_true(k_work_delayable_is_pending(&work),
		     "work should be pending before its delay elapses");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "handler did not signal completion");
	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_equal(atomic_get(&handler_ran_early), 0,
		      "handler ran before the requested delay, allowing one tick");
	zassert_false(k_work_delayable_is_pending(&work),
		      "completed work should no longer be pending");
}
