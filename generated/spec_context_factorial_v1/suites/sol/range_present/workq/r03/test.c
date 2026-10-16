#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define WORK_DELAY_MS 50

static K_SEM_DEFINE(work_done, 0, 1);
static atomic_t run_count;
static int64_t handler_time_ms;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&run_count);
	k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work, test_system_queue_delay)
{
	int64_t start_ms = k_uptime_get();
	int64_t tick_ms = k_ticks_to_ms_ceil64(1);

	zassert_equal(k_work_schedule(&delayed_work, K_MSEC(WORK_DELAY_MS)), 1,
		      "scheduling failed");
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work was not pending after scheduling");
	zassert_equal(atomic_get(&run_count), 0, "handler ran before the pending check");

	zassert_equal(k_sem_take(&work_done, K_MSEC(500)), 0,
		      "handler did not complete");
	zassert_true(handler_time_ms - start_ms >= WORK_DELAY_MS - tick_ms,
		     "handler ran before the requested delay");
	zassert_equal(atomic_get(&run_count), 1, "handler did not run exactly once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work remained pending after completion");

	k_sleep(K_MSEC(20));
	zassert_equal(atomic_get(&run_count), 1, "handler ran more than once");
}

ZTEST_SUITE(delayed_work, NULL, NULL, NULL, NULL, NULL);
