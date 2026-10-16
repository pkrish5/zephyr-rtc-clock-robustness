#include <zephyr/ztest.h>
#include <zephyr/kernel.h>

#define WORK_DELAY K_MSEC(20)
#define DELAY_TOLERANCE_TICKS 1

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

static void test_system_work_delayable_timing(void)
{
	const int64_t delay_ms = k_ticks_to_ms_floor64(k_ms_to_ticks_ceil64(20));
	const int64_t tick_granularity_ms = k_ticks_to_ms_ceil64(1);

	k_sem_reset(&work_done);
	atomic_set(&handler_count, 0);
	k_work_init_delayable(&delayed_work, delayed_work_handler);

	scheduled_at_ms = k_uptime_get();
	zassert_equal(k_work_schedule(&delayed_work, WORK_DELAY), 1,
		      "scheduling delayed work should succeed");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");
	zassert_equal(atomic_get(&handler_count), 0,
		      "handler should not have run immediately");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "work handler should complete within timeout");

	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_true(handler_at_ms - scheduled_at_ms >=
		     delay_ms - tick_granularity_ms,
		     "handler ran earlier than requested delay allows");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(system_work_delayable, NULL, NULL, NULL, NULL, NULL);

ZTEST(system_work_delayable, test_system_work_delayable_timing)
{
	test_system_work_delayable_timing();
}
