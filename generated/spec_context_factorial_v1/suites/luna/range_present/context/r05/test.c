#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP_MS 100
#define TEST_TIMEOUT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completion_sem;
static struct k_sem unrelated_sem;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sleep(K_MSEC(WORKER_SLEEP_MS));
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timeout)
{
	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);

	/* This unrelated signal must not be mistaken for worker completion. */
	k_sem_give(&unrelated_sem);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&unrelated_sem, K_NO_WAIT), 0,
		      "unrelated event should be available");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker must not complete immediately");

	int64_t start_ms = k_uptime_get();
	zassert_equal(k_sem_take(&completion_sem, K_MSEC(TEST_TIMEOUT_MS)), 0,
		      "worker completion event should arrive");
	int64_t elapsed_ms = k_uptime_get() - start_ms;
	zassert_true(elapsed_ms >= WORKER_SLEEP_MS,
		     "completion arrived before the requested sleep interval");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
