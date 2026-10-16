#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_MSEC(50)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&started);
	k_sleep(SLEEP_TIME);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	k_sem_init(&started, 0, 1);
	k_sem_init(&completed, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	/* The immediate start signal is separate from the completion event. */
	zassert_equal(k_sem_take(&started, K_SECONDS(1)), 0);
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);

	zassert_equal(k_sem_take(&completed, K_SECONDS(2)), 0);
	zassert_true(sleep_end_ms - sleep_start_ms >= 50,
		     "worker completed before its sleep timeout");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
