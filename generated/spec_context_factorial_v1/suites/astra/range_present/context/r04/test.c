#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 100
#define WATCHDOG_MS 2000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entering_sleep;
static struct k_sem completed;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;
static int32_t sleep_result;

static void worker(void *p1, void *p2, void *p3)
{
	(void)p1;
	(void)p2;
	(void)p3;

	/*
	 * On this single CPU, this cooperative worker continues from the
	 * immediate notification into k_sleep() before the test can run.
	 */
	sleep_started_ms = k_uptime_get();
	k_sem_give(&entering_sleep);
	sleep_result = k_sleep(K_MSEC(SLEEP_MS));
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	int rc;
	int immediate_rc;
	int completion_rc;
	int join_rc;

	zassert_ok(k_sem_init(&entering_sleep, 0, 1),
		   "Failed to initialize entry semaphore");
	zassert_ok(k_sem_init(&completed, 0, 1),
		   "Failed to initialize completion semaphore");

	/* Establish that neither event was left pending before creation. */
	zassert_equal(k_sem_take(&entering_sleep, K_NO_WAIT), -EBUSY,
		      "Unexpected entry event");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected completion event");

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack),
				     worker, NULL, NULL, NULL,
				     K_PRIO_COOP(0), 0, K_NO_WAIT);

	/* This immediate signal is deliberately distinct from completion. */
	rc = k_sem_take(&entering_sleep, K_MSEC(WATCHDOG_MS));
	if (rc != 0) {
		k_thread_abort(tid);
	}
	zassert_ok(rc, "Worker did not reach its timed sleep");

	immediate_rc = k_sem_take(&completed, K_NO_WAIT);
	completion_rc = k_sem_take(&completed, K_MSEC(WATCHDOG_MS));
	join_rc = k_thread_join(tid, K_MSEC(WATCHDOG_MS));
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(immediate_rc, -EBUSY,
		      "Worker reported completion immediately");
	zassert_ok(completion_rc, "Timed sleep did not deliver completion");
	zassert_ok(join_rc, "Worker did not exit");
	zassert_equal(sleep_result, 0, "Sleep returned before timeout");

	/* Allow one millisecond for integer uptime conversion rounding. */
	zassert_true(sleep_finished_ms - sleep_started_ms >= SLEEP_MS - 1,
		     "Worker completed before the requested sleep elapsed");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected duplicate completion event");

	/*
	 * WATCHDOG_MS is a generous test failure deadline, not an asserted
	 * ISR-to-thread latency bound. Uptime uses the board's own clock;
	 * this test neither measures nor calibrates HSI accuracy.
	 */
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
