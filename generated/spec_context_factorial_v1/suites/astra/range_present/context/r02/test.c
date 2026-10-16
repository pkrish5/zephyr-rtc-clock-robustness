#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 50

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static int32_t sleep_remaining_ms;

static void worker(void *p1, void *p2, void *p3)
{
	(void)p1;
	(void)p2;
	(void)p3;

	/* This immediate notification is deliberately not completion. */
	k_sem_give(&entered);
	sleep_start_ms = k_uptime_get();
	sleep_remaining_ms = k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	int entered_rc;
	int immediate_rc;
	int completed_rc;
	int join_rc;

	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);
	sleep_start_ms = 0;
	sleep_end_ms = 0;
	sleep_remaining_ms = -1;

	/*
	 * On this single CPU, the cooperative worker continues from giving
	 * 'entered' until k_sleep() blocks it. The notification therefore
	 * cannot let the test preempt the worker before it enters sleep.
	 */
	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				    K_THREAD_STACK_SIZEOF(worker_stack),
				    worker, NULL, NULL, NULL,
				    K_PRIO_COOP(0), 0, K_NO_WAIT);

	entered_rc = k_sem_take(&entered, K_SECONDS(2));
	immediate_rc = k_sem_take(&completed, K_NO_WAIT);

	/*
	 * A generous liveness watchdog, not an ISR delivery-latency bound.
	 * Uptime measures kernel time; the HSI accuracy specification alone
	 * cannot establish a wall-clock delivery deadline.
	 */
	completed_rc = k_sem_take(&completed, K_SECONDS(2));
	join_rc = k_thread_join(tid, K_SECONDS(1));
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	/* Clean up the worker before any assertion can end the test. */
	zassert_equal(entered_rc, 0, "Worker did not announce entry");
	zassert_equal(immediate_rc, -EBUSY,
		      "Completion was available immediately after entry");
	zassert_equal(completed_rc, 0,
		      "No completion event after the sleep timeout");
	zassert_equal(join_rc, 0, "Worker did not terminate");
	zassert_equal(sleep_remaining_ms, 0, "Sleep ended prematurely");
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS,
		     "Worker completed before its requested sleep elapsed");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected duplicate completion event");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
