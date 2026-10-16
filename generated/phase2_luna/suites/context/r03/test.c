#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define TEST_TIMEOUT K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started_sem;
static struct k_sem completion_sem;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Publish that the worker is about to enter its timed sleep. */
	k_sem_give(&started_sem);
	k_sleep(WORKER_SLEEP);
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_timed_sleep_wakes_worker)
{
	int64_t start_ms;
	int64_t elapsed_ms;

	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&completion_sem, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Wait until the worker has announced its impending sleep. */
	zassert_ok(k_sem_take(&started_sem, TEST_TIMEOUT),
		   "worker did not start");

	/* The worker must not complete during the first part of its delay. */
	zassert_equal(k_sem_take(&completion_sem, K_MSEC(20)), -EAGAIN,
		      "worker completed before its sleep timeout");

	start_ms = k_uptime_get();
	zassert_ok(k_sem_take(&completion_sem, TEST_TIMEOUT),
		   "worker did not complete after sleeping");
	elapsed_ms = k_uptime_get() - start_ms;
	zassert_true(elapsed_ms >= 40,
		    "completion arrived too soon after the early check: %lld ms",
		    (long long)elapsed_ms);
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "completion event was delivered more than once");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
