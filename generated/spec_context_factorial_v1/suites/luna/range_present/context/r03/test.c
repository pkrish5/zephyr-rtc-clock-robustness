#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(50)
#define EVENT_WAIT_MAX K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completion_sem;
static struct k_sem unrelated_sem;
static volatile bool worker_entered_sleep;
static volatile int64_t worker_start_ms;
static volatile int64_t worker_wake_ms;

static void sleep_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	worker_start_ms = k_uptime_get();
	worker_entered_sleep = true;
	k_sleep(WORKER_SLEEP);
	worker_wake_ms = k_uptime_get();
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timed_sleep)
{
	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);
	worker_entered_sleep = false;
	worker_start_ms = 0;
	worker_wake_ms = 0;

	/* This signal must not be mistaken for the worker's completion. */
	k_sem_give(&unrelated_sem);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			sleep_worker, NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0,
			K_NO_WAIT);

	zassert_equal(k_sem_take(&unrelated_sem, K_NO_WAIT), 0,
		     "unrelated signal should be available");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
		     "worker completion must not be immediate");

	zassert_equal(k_sem_take(&completion_sem, EVENT_WAIT_MAX), 0,
		     "worker did not signal completion before timeout");
	zassert_true(worker_entered_sleep, "worker did not enter timed sleep");
	zassert_true(worker_wake_ms - worker_start_ms >= k_ticks_to_ms_ceil32(1),
		     "worker completion arrived without a timed delay");
	zassert_true(worker_wake_ms - worker_start_ms < 1000,
		     "worker sleep exceeded reasonable bound");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
		     "completion event should be delivered only once");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
