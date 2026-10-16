#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <errno.h>

#define SLEEP_MS 50
#define WAIT_LIMIT K_SECONDS(1)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered;
static struct k_sem completed;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* This immediate notification is distinct from completion. */
	k_sem_give(&entered);
	sleep_started_ms = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_timed_sleep_wakeup)
{
	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);
	sleep_started_ms = -1;
	sleep_finished_ms = -1;

	/* On one CPU, this cooperative worker cannot be preempted by
	 * the test between its entry notification and blocking in sleep.
	 */
	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), worker,
		NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	int entered_rc = k_sem_take(&entered, WAIT_LIMIT);
	int immediate_rc = k_sem_take(&completed, K_NO_WAIT);
	int completion_rc = k_sem_take(&completed, WAIT_LIMIT);
	int join_rc = k_thread_join(tid, WAIT_LIMIT);

	/* Clean up before assertions, including on a timeout. */
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(entered_rc, 0, "Worker did not announce entry");
	zassert_equal(immediate_rc, -EBUSY,
		      "Entry notification must not imply sleep completion");
	zassert_equal(completion_rc, 0,
		      "Worker did not deliver completion after sleep");
	zassert_equal(join_rc, 0, "Worker did not exit");
	zassert_true(sleep_started_ms >= 0, "Worker never began sleep");
	zassert_true(sleep_finished_ms - sleep_started_ms >= SLEEP_MS,
		     "Worker completed before the sleep timeout");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected duplicate completion");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
