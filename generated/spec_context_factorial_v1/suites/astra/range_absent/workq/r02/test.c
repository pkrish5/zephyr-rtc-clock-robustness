#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

#define DELAY_MS 50

static atomic_t execution_count;
static int64_t handler_time_ms;
K_SEM_DEFINE(completion, 0, 2);

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&execution_count);
	k_sem_give(&completion);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work_suite, test_timer_driven_work)
{
	int64_t start_ms;
	int64_t elapsed_ms;
	const int64_t tick_ms = (int64_t)k_ticks_to_ms_ceil64(1);
	int ret;

	atomic_set(&execution_count, 0);
	k_sem_reset(&completion);

	start_ms = k_uptime_get();
	ret = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	zassert_equal(ret, 1, "Fresh delayed work was not scheduled");

	/* The configured cooperative test thread does not yield here. */
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "Scheduled work is not pending");
	zassert_equal(atomic_get(&execution_count), 0,
		      "Handler ran before the initial pending check");

	ret = k_sem_take(&completion, K_SECONDS(1));
	zassert_equal(ret, 0, "Timed out waiting for delayed work");
	zassert_equal(atomic_get(&execution_count), 1,
		      "Handler did not execute exactly once");

	elapsed_ms = handler_time_ms - start_ms;
	/* Allow one tick, rounded up to milliseconds, for clock granularity. */
	zassert_true(elapsed_ms >= 0 && elapsed_ms + tick_ms >= DELAY_MS,
		     "Handler ran too early: elapsed %lld ms",
		     (long long)elapsed_ms);

	/*
	 * With the fixed cooperative priorities, the system workqueue runs
	 * through handler return before this test thread can resume.
	 */
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work remains pending");

	ret = k_sem_take(&completion, K_MSEC(2 * DELAY_MS));
	zassert_equal(ret, -EAGAIN, "Unexpected additional execution");
	zassert_equal(atomic_get(&execution_count), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work became pending again");
}

ZTEST_SUITE(delayed_work_suite, NULL, NULL, NULL, NULL, NULL);
