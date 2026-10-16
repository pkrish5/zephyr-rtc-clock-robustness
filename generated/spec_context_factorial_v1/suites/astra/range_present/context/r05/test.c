#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 50
#define WAIT_MS 2000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static int32_t sleep_result;

static void sleeper(void *p1, void *p2, void *p3)
{
	(void)p1;
	(void)p2;
	(void)p3;

	/* On this single CPU, prevent the test from running between the
	 * entry signal and k_sleep(). Blocking releases the CPU even while
	 * scheduling is locked; the lock remains held when we resume.
	 */
	k_sched_lock();
	sleep_start_ms = k_uptime_get();
	k_sem_give(&entered);
	sleep_result = k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
	k_sched_unlock();
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	int entered_rc;
	int immediate_rc;
	int completion_rc;
	int join_rc;
	k_tid_t tid;

	zassert_equal(k_sem_init(&entered, 0, 1), 0,
		      "Entry semaphore initialization failed");
	zassert_equal(k_sem_init(&completed, 0, 1), 0,
		      "Completion semaphore initialization failed");

	sleep_start_ms = 0;
	sleep_end_ms = 0;
	sleep_result = -1;

	tid = k_thread_create(&worker_thread, worker_stack,
			      K_THREAD_STACK_SIZEOF(worker_stack),
			      sleeper, NULL, NULL, NULL,
			      K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	/* The immediate entry signal is deliberately a different event
	 * from sleep completion. Consuming it cannot satisfy completed.
	 */
	entered_rc = k_sem_take(&entered, K_MSEC(WAIT_MS));
	immediate_rc = k_sem_take(&completed, K_NO_WAIT);
	completion_rc = (immediate_rc == 0) ? 0 :
		k_sem_take(&completed, K_MSEC(WAIT_MS));

	/* Finish cleanup before assertions, including on failure paths. */
	join_rc = k_thread_join(tid, K_MSEC(WAIT_MS));
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(entered_rc, 0, "Worker did not enter timed sleep");
	zassert_equal(immediate_rc, -EBUSY,
		      "Worker completion was already available at sleep entry");
	zassert_equal(completion_rc, 0,
		      "Worker did not deliver completion after its timeout");
	zassert_equal(join_rc, 0, "Worker did not terminate");
	zassert_equal(sleep_result, 0, "Worker sleep ended prematurely");

	/* Measure kernel time, not independently calibrated wall time.
	 * WAIT_MS is a generous test watchdog, not an ISR-to-thread
	 * latency bound inferred from the HSI oscillator tolerance.
	 */
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS,
		     "Completion preceded the requested sleep interval");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected extra completion event");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
