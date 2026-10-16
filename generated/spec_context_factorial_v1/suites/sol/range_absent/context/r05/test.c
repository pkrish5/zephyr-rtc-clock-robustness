#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 40

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_sem ready_sem;
static struct k_sem done_sem;
static int64_t sleep_started;
static int64_t sleep_ended;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* This immediate signal is distinct from the completion event. */
	k_sem_give(&ready_sem);
	sleep_started = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_ended = k_uptime_get();
	k_sem_give(&done_sem);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	k_sem_init(&ready_sem, 0, 1);
	k_sem_init(&done_sem, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&ready_sem, K_MSEC(100)));
	zassert_not_equal(k_sem_take(&done_sem, K_NO_WAIT), 0);
	zassert_not_equal(k_sem_take(&done_sem, K_MSEC(10)), 0);
	zassert_ok(k_sem_take(&done_sem, K_MSEC(200)));
	zassert_true(sleep_ended - sleep_started >= 30,
		     "worker completed before its timed sleep elapsed");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
