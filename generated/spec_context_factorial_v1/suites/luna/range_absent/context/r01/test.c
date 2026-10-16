#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 50
#define TEST_TIMEOUT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started_sem;
static struct k_sem unrelated_sem;
static struct k_sem completed_sem;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Announce entry immediately before beginning the timed sleep. */
	k_sem_give(&started_sem);
	k_sleep(K_MSEC(SLEEP_MS));
	k_sem_give(&completed_sem);
}

ZTEST(timer_sleep_wakeup, test_timed_sleep_wakeup)
{
	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Wait until the worker is about to sleep, then issue a distinct signal. */
	zassert_equal(k_sem_take(&started_sem, K_MSEC(TEST_TIMEOUT_MS)), 0,
		      "worker did not start");
	k_sem_give(&unrelated_sem);

	/* The completion event must not be available before the sleep expires. */
	zassert_equal(k_sem_take(&completed_sem, K_NO_WAIT), -EAGAIN,
		      "worker completed immediately");
	zassert_equal(k_sem_take(&unrelated_sem, K_NO_WAIT), 0,
		      "unrelated signal was not received");
	zassert_equal(k_sem_take(&completed_sem, K_MSEC(TEST_TIMEOUT_MS)), 0,
		      "worker did not complete after its timed sleep");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
