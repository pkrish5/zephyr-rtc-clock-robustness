#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

#define SLEEP_MS 50

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered;
static struct k_sem completed;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	sleep_started_ms = k_uptime_get();
	k_sem_give(&entered);
	/* Cooperative execution on one CPU prevents the test from running
	 * between the entry signal and this blocking call.
	 */
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_timeout_wakes_worker)
{
	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				    K_THREAD_STACK_SIZEOF(worker_stack),
				    sleeper, NULL, NULL, NULL,
				    K_PRIO_COOP(0), 0, K_NO_WAIT);

	/* The immediate entry signal must not count as completion. */
	zassert_equal(k_sem_take(&entered, K_SECONDS(1)), 0,
		      "Worker did not reach timed sleep");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Worker completed immediately instead of sleeping");

	zassert_equal(k_sem_take(&completed, K_SECONDS(1)), 0,
		      "Worker did not signal completion after its timeout");
	zassert_equal(k_thread_join(tid, K_SECONDS(1)), 0,
		      "Worker did not terminate");

	zassert_true(sleep_finished_ms - sleep_started_ms >= SLEEP_MS,
		     "Worker resumed before the requested sleep elapsed");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Unexpected additional completion event");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
