#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_MSEC(100)
#define EVENT_TIMEOUT K_SECONDS(2)
#define WORKER_PRIORITY 5

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered_sem;
static struct k_sem completion_sem;
static int64_t sleep_start_ms;
static int64_t wake_ms;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&entered_sem);
	k_sleep(SLEEP_TIME);
	wake_ms = k_uptime_get();
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep, test_timed_sleep_wakes_worker)
{
	k_sem_init(&entered_sem, 0, 1);
	k_sem_init(&completion_sem, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);

	/* This event confirms the worker is about to enter its timed sleep. */
	zassert_ok(k_sem_take(&entered_sem, EVENT_TIMEOUT),
		   "worker did not start");

	/* A separate completion semaphore prevents the entry event from being
	 * mistaken for completion.
	 */
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker completed before its sleep timeout");

	zassert_ok(k_sem_take(&completion_sem, EVENT_TIMEOUT),
		   "completion event did not arrive");
	zassert_true(wake_ms - sleep_start_ms >= 100,
		     "worker woke before the requested sleep duration");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
