#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>

#define DELAY_MS 50
#define COMPLETION_TIMEOUT_MS 2000

static K_SEM_DEFINE(completed, 0, 2);
static atomic_t handler_calls;
static int64_t first_handler_ms;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);

	if (atomic_inc(&handler_calls) == 0) {
		first_handler_ms = k_uptime_get();
	}
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work_test, test_timer_driven_execution)
{
	int schedule_result;
	bool initially_pending;
	int64_t start_ms;
	int64_t elapsed_ms;
	const int64_t tick_ms = (int64_t)k_ticks_to_ms_ceil64(1);
	unsigned int key;

	atomic_set(&handler_calls, 0);
	first_handler_ms = -1;
	k_sem_reset(&completed);

	/* Observe initial state before the timer can dispatch the work. */
	key = irq_lock();
	start_ms = k_uptime_get();
	schedule_result = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	initially_pending = k_work_delayable_is_pending(&delayed_work);
	irq_unlock(key);

	zassert_equal(schedule_result, 1, "Fresh work was not scheduled");
	zassert_true(initially_pending, "Scheduled work was not pending");
	/* The configured cooperative test thread has not blocked yet. */
	zassert_equal(atomic_get(&handler_calls), 0,
		      "Handler ran before the test blocked");

	/* This timeout is a test budget, not a hardware delivery bound. */
	zassert_equal(k_sem_take(&completed, K_MSEC(COMPLETION_TIMEOUT_MS)),
		      0, "Handler did not signal completion");

	/*
	 * On this single CPU, the cooperative system workqueue finishes its
	 * handler before the awakened cooperative test thread can resume.
	 */
	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler did not execute exactly once");
	elapsed_ms = first_handler_ms - start_ms;
	/*
	 * Uptime is tick based. Allow one tick rounded up to milliseconds
	 * for sampling/quantization. This checks kernel time, not external
	 * wall-clock accuracy or an ISR-to-thread latency bound.
	 */
	zassert_true(elapsed_ms >= 0 && elapsed_ms + tick_ms >= DELAY_MS,
		     "Handler was observed before the requested delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work remained pending after completion");

	/* Observe another two delay intervals for unintended repetition. */
	zassert_equal(k_sem_take(&completed, K_MSEC(2 * DELAY_MS)),
		      -EAGAIN, "Unexpected additional handler completion");
	zassert_equal(atomic_get(&handler_calls), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
