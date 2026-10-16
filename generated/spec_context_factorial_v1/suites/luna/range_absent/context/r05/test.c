#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP_MS 100
#define EVENT_TIMEOUT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem sleep_started;
static struct k_sem completion_event;
static struct k_sem unrelated_event;
static int64_t worker_sleep_started_at;

static void sleep_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	worker_sleep_started_at = k_uptime_get();
	k_sem_give(&sleep_started);
	k_sleep(K_MSEC(WORKER_SLEEP_MS));
	k_sem_give(&completion_event);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timed_sleep)
{
	k_sem_init(&sleep_started, 0, 1);
	k_sem_init(&completion_event, 0, 1);
	k_sem_init(&unrelated_event, 0, 1);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			worker_sleep, NULL, NULL, NULL,
			K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Wait until the worker is about to sleep; its lower priority lets it
	 * block in k_sleep() before this test thread runs again.
	 */
	zassert_ok(k_sem_take(&sleep_started, K_MSEC(EVENT_TIMEOUT_MS)),
		   "worker did not start its timed sleep");

	/* An unrelated immediate event must not be mistaken for completion. */
	k_sem_give(&unrelated_event);
	zassert_ok(k_sem_take(&unrelated_event, K_NO_WAIT),
		   "unrelated event was not delivered");
	zassert_equal(k_sem_take(&completion_event, K_NO_WAIT), -EBUSY,
		      "worker completed before its sleep timeout");

	zassert_ok(k_sem_take(&completion_event, K_MSEC(EVENT_TIMEOUT_MS)),
		   "completion event did not arrive after the timeout");
	zassert_true(k_uptime_get() - worker_sleep_started_at >= WORKER_SLEEP_MS,
		     "completion arrived before the worker sleep timeout");
	zassert_equal(k_sem_take(&unrelated_event, K_NO_WAIT), -EBUSY,
		      "unrelated event was confused with worker completion");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
