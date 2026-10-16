#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

#define DELAY_MS 50

static K_SEM_DEFINE(completed, 0, 1);
static atomic_t handler_count;
static int64_t handler_time_ms;

static void delayed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	handler_time_ms = k_uptime_get();
	atomic_inc(&handler_count);
	k_sem_give(&completed);
}

static K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work_test, test_timer_driven_work)
{
	struct k_work_sync sync = {0};
	int64_t start_ms;
	int64_t tick_ms = k_ticks_to_ms_ceil64(1);
	int ret;

	atomic_set(&handler_count, 0);
	k_sem_reset(&completed);
	handler_time_ms = 0;

	start_ms = k_uptime_get();
	ret = k_work_schedule(&delayed_work, K_MSEC(DELAY_MS));
	zassert_equal(ret, 1, "Fresh delayed work was not scheduled");

	/* Both threads are cooperative: the handler cannot run until we block. */
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "Scheduled work must be pending");
	zassert_equal(atomic_get(&handler_count), 0,
		      "Handler ran before the initial pending check");

	ret = k_sem_take(&completed, K_SECONDS(1));
	zassert_equal(ret, 0, "Timed out waiting for delayed work");

	/* Ensure the handler has returned before inspecting completion state. */
	(void)k_work_flush_delayable(&delayed_work, &sync);
	zassert_equal(atomic_get(&handler_count), 1,
		      "Handler must execute exactly once");

	/* Uptime is tick-based; allow one tick, rounded up to milliseconds. */
	zassert_true(handler_time_ms - start_ms >= (int64_t)DELAY_MS - tick_ms,
		     "Handler was observed earlier than the allowed delay");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Completed work must no longer be pending");

	/* Observe another two delay intervals to detect an unexpected repeat. */
	ret = k_sem_take(&completed, K_MSEC(2 * DELAY_MS));
	zassert_equal(ret, -EAGAIN, "Unexpected additional completion");
	zassert_equal(atomic_get(&handler_count), 1,
		      "Handler executed more than once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "Work unexpectedly became pending again");
}

ZTEST_SUITE(delayed_work_test, NULL, NULL, NULL, NULL, NULL);
