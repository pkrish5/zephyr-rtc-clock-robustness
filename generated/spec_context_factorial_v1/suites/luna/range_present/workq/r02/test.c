#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORK_DELAY K_MSEC(100)
#define DELAY_MS 100

static struct k_work_delayable delayed_work;
static struct k_sem work_done;
static atomic_t handler_count;
static int64_t handler_time_ms;

static void delayed_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&work_done);
}

ZTEST(delayable_work, test_timer_driven_delay)
{
	int64_t scheduled_at;

	k_sem_reset(&work_done);
	atomic_set(&handler_count, 0);
	handler_time_ms = 0;
	k_work_init_delayable(&delayed_work, delayed_work_handler);
	scheduled_at = k_uptime_get();

	zassert_ok(k_work_schedule(&delayed_work, WORK_DELAY), "schedule failed");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");

	zassert_equal(k_sem_take(&work_done, K_SECONDS(2)), 0,
		      "timed out waiting for delayed work");

	zassert_equal(atomic_get(&handler_count), 1, "handler should run exactly once");
	/* Allow one system tick of quantization when checking the requested delay. */
	zassert_true(handler_time_ms - scheduled_at >= DELAY_MS - k_ticks_to_ms_floor32(1),
		     "handler ran before the requested delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
