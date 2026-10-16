#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP_MS 50
#define TEST_TIMEOUT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completion_sem;
static struct k_sem started_sem;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Report that the worker reached the point immediately before sleeping. */
	k_sem_give(&started_sem);
	k_sleep(K_MSEC(WORKER_SLEEP_MS));
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_timer_driven_sleep_and_wakeup)
{
	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&started_sem, 0, 1);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			 sleep_worker, NULL, NULL, NULL,
			 K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Wait until the worker is about to sleep, then ensure no event is pending. */
	zassert_equal(k_sem_take(&started_sem, K_MSEC(TEST_TIMEOUT_MS)), 0,
		       "worker did not start");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
		       "worker completed immediately");

	int64_t start_ms = k_uptime_get();
	zassert_equal(k_sem_take(&completion_sem, K_MSEC(TEST_TIMEOUT_MS)), 0,
		       "worker completion event timed out");
	int64_t elapsed_ms = k_uptime_get() - start_ms;

	zassert_true(elapsed_ms >= WORKER_SLEEP_MS,
		     "completion arrived too early: %lld ms", (long long)elapsed_ms);
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
		       "unexpected extra completion event");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
