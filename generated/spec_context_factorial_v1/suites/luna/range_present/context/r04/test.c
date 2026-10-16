#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define COMPLETION_TIMEOUT K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started_sem;
static struct k_sem completed_sem;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&started_sem);
	k_sleep(WORKER_SLEEP);
	k_sem_give(&completed_sem);
}

ZTEST(timer_sleep, test_thread_wakes_after_timed_sleep)
{
	const int64_t sleep_ms = 100;
	int64_t start_ms;

	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);

	start_ms = k_uptime_get();
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	/* The start event confirms the worker ran; completion has its own semaphore. */
	zassert_equal(k_sem_take(&started_sem, K_SECONDS(1)), 0,
		      "worker did not start");
	zassert_equal(k_sem_take(&completed_sem, K_NO_WAIT), -EAGAIN,
		      "worker reported completion immediately");

	zassert_equal(k_sem_take(&completed_sem, COMPLETION_TIMEOUT), 0,
		      "worker did not complete before the deadline");
	zassert_true(k_uptime_get() - start_ms >= sleep_ms,
		     "completion arrived before the sleep timeout");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
