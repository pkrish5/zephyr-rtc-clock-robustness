#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_MSEC(50)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem immediate_sem;
static struct k_sem start_sem;
static struct k_sem completion_sem;
static int64_t worker_sleep_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&immediate_sem);
	k_sem_take(&start_sem, K_FOREVER);

	int64_t before = k_uptime_get();
	k_sleep(SLEEP_TIME);
	worker_sleep_ms = k_uptime_get() - before;
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	k_sem_init(&immediate_sem, 0, 1);
	k_sem_init(&start_sem, 0, 1);
	k_sem_init(&completion_sem, 0, 1);
	worker_sleep_ms = 0;

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, 5, 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&immediate_sem, K_MSEC(200)), 0,
		      "worker did not signal readiness");
	zassert_not_equal(k_sem_take(&completion_sem, K_NO_WAIT), 0,
			  "completion arrived before timed sleep");

	k_sem_give(&start_sem);
	zassert_equal(k_sem_take(&completion_sem, K_MSEC(500)), 0,
		      "worker did not complete after timed sleep");
	zassert_true(worker_sleep_ms >= 40,
		     "worker completed before the sleep interval elapsed");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
