#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORK_DELAY K_MSEC(20)
#define MAX_HANDLER_EARLY_TICKS 1

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

static void test_delayable_work_on_system_queue(void)
{
	const int64_t delay_ms = k_ticks_to_ms_floor64(k_ms_to_ticks_ceil64(20));
	int64_t elapsed_ms;

	k_sem_reset(&work_done);
	atomic_set(&handler_count, 0);
	handler_at_ms = -1;

	zassert_ok(k_work_schedule(&delayed_work, WORK_DELAY),
		   "scheduling delayed work failed");
	scheduled_at_ms = k_uptime_get();
	zassert_true(k_work_delayable_is_pending(&delayed_work),
		     "work should be pending immediately after scheduling");
	zassert_equal(atomic_get(&handler_count), 0,
		      "handler ran before the delay elapsed");

	zassert_ok(k_sem_take(&work_done, K_SECONDS(2)),
		   "timed out waiting for delayed work");

	elapsed_ms = handler_at_ms - scheduled_at_ms;
	zassert_true(elapsed_ms >= delay_ms - MAX_HANDLER_EARLY_TICKS,
		     "handler ran too early: elapsed %lld ms, delay %lld ms",
		     (long long)elapsed_ms, (long long)delay_ms);
	zassert_equal(atomic_get(&handler_count), 1,
		      "handler should execute exactly once");
	zassert_false(k_work_delayable_is_pending(&delayed_work),
		      "work should no longer be pending after completion");
}

static void *work_test_setup(void)
{
	k_sem_init(&work_done, 0, 1);
	k_work_init_delayable(&delayed_work, delayed_work_handler);
	atomic_set(&handler_count, 0);
	return NULL;
}

ZTEST_SUITE(delayable_work_system_queue, NULL, work_test_setup, NULL, NULL, NULL);

ZTEST(delayable_work_system_queue, test_delayable_work_on_system_queue)
{
	test_delayable_work_on_system_queue();
}
