#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 50
#define WAIT_MS 500

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_sem sleep_started;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t wake_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&sleep_started);
	k_sleep(K_MSEC(SLEEP_MS));
	wake_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_thread_wakes_after_timeout)
{
	k_sem_init(&sleep_started, 0, 1);
	k_sem_init(&completed, 0, 1);

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack), worker,
				     NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0,
				     K_NO_WAIT);

	zassert_not_null(tid);
	zassert_equal(k_sem_take(&sleep_started, K_MSEC(WAIT_MS)), 0);
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0,
			  "worker completed immediately");
	zassert_equal(k_sem_take(&completed, K_MSEC(WAIT_MS)), 0,
			      "worker did not complete after sleep");
	zassert_true(wake_ms - sleep_start_ms >= 25,
		     "completion arrived before the sleep timeout");
	zassert_equal(k_thread_join(tid, K_MSEC(WAIT_MS)), 0);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
