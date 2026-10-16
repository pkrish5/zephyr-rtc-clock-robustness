#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/irq.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys_clock.h>
#include <stdbool.h>
#include <stdint.h>

#define DELAY_MS 50

static struct k_work_delayable delayed_work;
static K_SEM_DEFINE(completed, 0, 2);
static atomic_t handler_count;
static int64_t handler_time_ms;
static struct k_work_sync work_sync;

static void work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&completed);
}

ZTEST(delayed_work_test, test_timer_driven_system_work)
{
	int schedule_rc;
	int completion_rc;
	bool pending_before;
	int64_t start_ms;
	unsigned int key;
	const int64_t tick_ms = (int64_t)k_ticks_to_ms_ceil64(1);

	k_sem_reset(&completed);
	atomic_clear(&handler_count);
	handler_time_ms = -1;
	k_work_init_delayable(&delayed_work, work_handler);

	/* On this single CPU, prevent timeout delivery until sampled. */
	key = irq_lock();
	start_ms = k_uptime_get();
	schedule_rc = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	pending_before = k_work_delayable_is_pending(&delayed_work);
	irq_unlock(key);

	/* This is a test watchdog, not a hardware delivery-latency bound. */
	completion_rc = k_sem_take(&completed, K_SECONDS(5));
	if (completion_rc != 0) {
		(void)k_work_cancel_delayable_sync(&delayed_work, &work_sync);
	}

	zassert_equal(schedule_rc, 1, "Idle work was not newly scheduled");
	zassert_true(pending_before, "Scheduled work was not pending");
	zassert_equal(completion_rc, 0, "Handler did not signal completion");

	/* The semaphore signals inside the handler; wait for its return too. */
	(void)k_work_flush_delayable(&delayed_work, &work_sync);

	zassert_equal(atomic_get(&handler_count), 1,
		      "Handler must execute exactly once");

	/*
	 * Use the same kernel clock for scheduling and observation. Allow one
	 * tick, rounded upward to milliseconds, for tick/millisecond granularity.
	 * HSI accuracy does not establish an ISR-to-thread latency bound, so
	 * there is no assertion on maximum dispatch lateness.
	 */
	zassert_true(handler_time_ms - start_ms >= DELAY_MS - tick_ms,
		     "Handler was observed before the requested delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work remains pending after completion");
	zassert_equal(k_sem_count_get(&completed), 0,
		      "Unexpected additional completion");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
