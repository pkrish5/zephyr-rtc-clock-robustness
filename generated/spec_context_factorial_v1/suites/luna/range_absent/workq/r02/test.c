#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TEST_DELAY K_MSEC(50)
#define TICK_GRACE_MS 1

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

ZTEST(delayable_work, test_system_workqueue_delay)
{
	k_sem_init(&work_done, 0, 1);
	atomic_set(&handler_count, 0);
	handler_at_ms = -1;
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	scheduled_at_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, TEST_DELAY), 1,
		      "scheduling delayable work should succeed");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "work handler should complete within the timeout");
	zassert_equal(atomic_get(&handler_count), 1,
		      "work handler should execute exactly once");
	zassert_true(handler_at_ms - scheduled_at_ms >=
		     (int64_t)k_ticks_to_ms_ceil32(K_MSEC(50).ticks) - TICK_GRACE_MS,
		     "work handler ran before the requested delay, allowing tick granularity");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should not be pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
