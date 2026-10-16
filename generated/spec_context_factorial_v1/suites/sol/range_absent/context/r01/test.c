#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_MSEC(50)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started;
static struct k_sem completed;
static struct k_sem unrelated;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&started);
	k_sleep(SLEEP_TIME);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_worker_wakes_after_timer_timeout)
{
	k_sem_init(&started, 0, 1);
	k_sem_init(&completed, 0, 1);
	k_sem_init(&unrelated, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&started, K_MSEC(500)),
		   "worker did not reach timed sleep");
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0,
			  "worker completed immediately");

	k_sem_give(&unrelated);
	zassert_ok(k_sem_take(&unrelated, K_NO_WAIT),
		   "unrelated immediate signal was not delivered");
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0,
			  "unrelated signal satisfied completion");

	zassert_ok(k_sem_take(&completed, K_MSEC(500)),
		   "worker did not complete after timed sleep");
	zassert_true(sleep_end_ms - sleep_start_ms >= 45,
		     "worker completed before the sleep interval elapsed");
	zassert_ok(k_thread_join(&worker_thread, K_MSEC(100)),
		   "worker thread did not exit");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
