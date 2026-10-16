#include <errno.h>
#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_MSEC(50)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem sleep_started;
static struct k_sem sleep_done;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&sleep_started);
	k_sleep(SLEEP_TIME);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&sleep_done);
}

ZTEST(timer_sleep, test_thread_wakes_after_timer_timeout)
{
	k_tid_t tid;

	zassert_equal(k_sem_init(&sleep_started, 0, 1), 0);
	zassert_equal(k_sem_init(&sleep_done, 0, 1), 0);

	tid = k_thread_create(&worker_thread, worker_stack,
			      K_THREAD_STACK_SIZEOF(worker_stack), worker,
			      NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&sleep_started, K_SECONDS(1)), 0,
		      "worker did not reach timed sleep");
	zassert_not_equal(k_sem_take(&sleep_done, K_NO_WAIT), 0,
			  "completion was already signaled");
	zassert_equal(k_sem_take(&sleep_done, K_MSEC(5)), -EAGAIN,
		      "completion arrived immediately");
	zassert_equal(k_sem_take(&sleep_done, K_SECONDS(2)), 0,
		      "worker did not signal completion");
	zassert_true(sleep_end_ms - sleep_start_ms >= 40,
		     "completion did not follow the sleep timeout");
	zassert_equal(k_thread_join(tid, K_MSEC(100)), 0);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
