#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 100
#define WAIT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started;
static struct k_sem completed;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/*
	 * Cooperative execution on one CPU means the test cannot run
	 * between this immediate signal and the following timed sleep.
	 */
	k_sem_give(&started);
	sleep_started_ms = k_uptime_get();
	(void)k_sleep(K_MSEC(SLEEP_MS));
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	zassert_equal(k_sem_init(&started, 0, 1), 0,
		      "Failed to initialize started semaphore");
	zassert_equal(k_sem_init(&completed, 0, 1), 0,
		      "Failed to initialize completion semaphore");

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack),
				     worker, NULL, NULL, NULL,
				     K_PRIO_COOP(0), 0, K_NO_WAIT);

	int ready_rc = k_sem_take(&started, K_MSEC(WAIT_MS));
	int immediate_rc = k_sem_take(&completed, K_NO_WAIT);
	int completion_rc = k_sem_take(&completed, K_MSEC(WAIT_MS));
	int64_t observed_ms = k_uptime_get();
	int join_rc = k_thread_join(tid, K_MSEC(WAIT_MS));

	/* Clean up even when an assertion below will fail. */
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(ready_rc, 0, "Worker did not reach timed sleep");
	zassert_equal(immediate_rc, -EBUSY,
		      "Immediate started signal must not imply completion");
	zassert_equal(completion_rc, 0,
		      "Worker did not deliver completion after timeout");
	zassert_equal(join_rc, 0, "Worker did not terminate");
	zassert_true(sleep_finished_ms - sleep_started_ms >= SLEEP_MS,
		     "Worker resumed before its sleep timeout");
	zassert_true(observed_ms - sleep_started_ms >= SLEEP_MS,
		     "Completion was observed before the sleep timeout");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
