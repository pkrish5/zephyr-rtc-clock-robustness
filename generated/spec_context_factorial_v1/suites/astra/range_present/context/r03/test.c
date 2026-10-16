#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 50
#define WATCHDOG_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered_sem;
static struct k_sem completed_sem;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *p1, void *p2, void *p3)
{
	(void)p1;
	(void)p2;
	(void)p3;

	/* This immediate signal is deliberately separate from completion. */
	k_sem_give(&entered_sem);
	sleep_start_ms = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed_sem);
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	int entered_rc;
	int immediate_rc;
	int completion_rc;
	int join_rc;

	k_sem_init(&entered_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);
	sleep_start_ms = 0;
	sleep_end_ms = 0;

	/*
	 * On this single-CPU target, the cooperative worker cannot be
	 * preempted by the test between giving entered_sem and sleeping.
	 * Thus receipt of entered_sem lets the test probe completion while
	 * the worker is in its timed sleep.
	 */
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	entered_rc = k_sem_take(&entered_sem, K_MSEC(WATCHDOG_MS));
	if (entered_rc != 0) {
		k_thread_abort(&worker_thread);
		zassert_equal(entered_rc, 0, "Worker did not reach timed sleep");
		return;
	}

	immediate_rc = k_sem_take(&completed_sem, K_NO_WAIT);
	completion_rc = (immediate_rc == 0) ? 0 :
		k_sem_take(&completed_sem, K_MSEC(WATCHDOG_MS));

	/* Reap the worker before assertions, including failure paths. */
	join_rc = k_thread_join(&worker_thread, K_MSEC(WATCHDOG_MS));
	if (join_rc != 0) {
		k_thread_abort(&worker_thread);
	}

	zassert_equal(immediate_rc, -EBUSY,
		      "Completion was already available after the entry signal");
	zassert_equal(completion_rc, 0,
		      "No completion event arrived after timed sleep");
	zassert_equal(join_rc, 0, "Worker did not terminate");
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS,
		     "Worker resumed before the requested timeout");

	/*
	 * Uptime checks elapsed kernel time, not absolute clock accuracy.
	 * WATCHDOG_MS is a generous test liveness limit, not an ISR-to-thread
	 * latency guarantee derived from the HSI's nominal 16 MHz +/-1%.
	 */
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
