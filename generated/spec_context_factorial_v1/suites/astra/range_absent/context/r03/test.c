#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>

#define SLEEP_MS 100

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static int32_t sleep_remaining_ms;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* On this single CPU, the test cannot resume until we block. */
	k_sched_lock();
	k_sem_give(&entered);
	sleep_start_ms = k_uptime_get();
	sleep_remaining_ms = k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
	k_sched_unlock();
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), sleeper,
		NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	int entered_rc = k_sem_take(&entered, K_SECONDS(1));
	int immediate_rc = k_sem_take(&completed, K_NO_WAIT);
	int completion_rc = immediate_rc;

	if (immediate_rc != 0) {
		completion_rc = k_sem_take(&completed, K_SECONDS(1));
	}

	int join_rc = k_thread_join(tid, K_SECONDS(1));

	/* Ensure that even a failing test leaves no running worker. */
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(entered_rc, 0, "Worker did not reach timed sleep");
	/* The immediate entry signal must not count as completion. */
	zassert_equal(immediate_rc, -EBUSY,
		      "Worker completion was available immediately");
	zassert_equal(completion_rc, 0, "Timed wakeup event did not arrive");
	zassert_equal(join_rc, 0, "Worker did not terminate");
	zassert_equal(sleep_remaining_ms, 0, "Sleep ended prematurely");
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS,
		     "Worker reported completion before the timeout");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected extra completion event");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
