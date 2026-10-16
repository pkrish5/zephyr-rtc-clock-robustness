#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define DELAY_MS 80

K_SEM_DEFINE(work_done, 0, 1);
static atomic_t handler_runs;
static int64_t handler_time_ms;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_runs);
	k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work, runs_once_after_delay)
{
	int64_t scheduled_at_ms = k_uptime_get();
	const int64_t tick_ms =
		(1000 + CONFIG_SYS_CLOCK_TICKS_PER_SEC - 1) /
		CONFIG_SYS_CLOCK_TICKS_PER_SEC;

	zassert_equal(k_work_schedule(&delayed_work, K_MSEC(DELAY_MS)), 1);
	zassert_true(k_work_delayable_is_pending(&delayed_work));

	zassert_equal(k_sem_take(&work_done, K_MSEC(DELAY_MS * 3)), 0);
	zassert_equal(atomic_get(&handler_runs), 1);
	zassert_true(handler_time_ms - scheduled_at_ms + tick_ms >= DELAY_MS);
	zassert_false(k_work_delayable_is_pending(&delayed_work));

	k_sleep(K_MSEC(DELAY_MS));
	zassert_equal(atomic_get(&handler_runs), 1);
	zassert_false(k_work_delayable_is_pending(&delayed_work));
}

ZTEST_SUITE(delayed_work, NULL, NULL, NULL, NULL, NULL);
