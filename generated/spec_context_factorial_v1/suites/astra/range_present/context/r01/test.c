#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 100
#define WATCHDOG_MS 2000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem startup_event;
static struct k_sem completion_event;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/*
	 * On this single CPU, scheduling remains locked between the startup
	 * signal and blocking in k_sleep(). Thus receiving startup_event
	 * lets the test observe the worker's timed sleep, not a preemption
	 * before it calls k_sleep(). Interrupts remain enabled.
	 */
	k_sched_lock();
	k_sem_give(&startup_event);
	sleep_started_ms = k_uptime_get();
	(void)k_sleep(K_MSEC(SLEEP_MS));
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&completion_event);
	k_sched_unlock();
}

ZTEST(timer_sleep, test_timeout_delivers_completion)
{
	int startup_rc;
	int immediate_rc;
	int completion_rc;

	zassert_equal(k_sem_init(&startup_event, 0, 1), 0);
	zassert_equal(k_sem_init(&completion_event, 0, 1), 0);
	sleep_started_ms = -1;
	sleep_finished_ms = -1;

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack),
				     worker, NULL, NULL, NULL,
				     K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	/* Startup is an immediate signal, deliberately separate from completion. */
	startup_rc = k_sem_take(&startup_event, K_MSEC(WATCHDOG_MS));
	immediate_rc = k_sem_take(&completion_event, K_NO_WAIT);
	completion_rc = k_sem_take(&completion_event, K_MSEC(WATCHDOG_MS));

	/* Clean up before assertions, including on a timeout or early signal. */
	k_thread_abort(tid);

	zassert_equal(startup_rc, 0, "Worker did not signal startup");
	zassert_equal(immediate_rc, -EBUSY,
		      "Completion was available immediately after startup");
	zassert_equal(completion_rc, 0,
		      "No completion event after the sleep timeout");
	zassert_true(sleep_started_ms >= 0, "Worker never started sleeping");
	zassert_true(sleep_finished_ms >= sleep_started_ms,
		     "Worker did not return from timed sleep");

	/* Allow one millisecond for integer uptime timestamp quantization. */
	zassert_true(sleep_finished_ms - sleep_started_ms >= SLEEP_MS - 1,
		     "Worker completed before the requested sleep elapsed");
	zassert_equal(k_sem_take(&completion_event, K_NO_WAIT), -EBUSY,
		      "Unexpected duplicate completion event");

	/*
	 * Uptime measures kernel time, not independently calibrated wall time.
	 * The watchdog bounds test execution; it is not an ISR-to-thread
	 * latency guarantee derived from the HSI clock's +/-1% accuracy.
	 */
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
