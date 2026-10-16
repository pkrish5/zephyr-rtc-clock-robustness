#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define TEST_WAIT K_MSEC(1000)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completion_sem;
static struct k_sem started_sem;
static struct k_sem unrelated_sem;
static int64_t sleep_started_ms;
static int64_t worker_finished_ms;

static void sleep_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	sleep_started_ms = k_uptime_get();
	k_sem_give(&started_sem);
	k_sleep(WORKER_SLEEP);
	worker_finished_ms = k_uptime_get();
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timeout)
{
	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);
	sleep_started_ms = -1;
	worker_finished_ms = -1;

	/* An unrelated event must not be mistaken for worker completion. */
	k_sem_give(&unrelated_sem);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&started_sem, TEST_WAIT), 0,
		      "worker did not enter its timed sleep");

	/* Completion must not be available while the worker is sleeping. */
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker completed immediately");
	zassert_true(k_sem_take(&unrelated_sem, K_NO_WAIT) == 0,
		     "unrelated signal was not present");
	zassert_equal(k_sem_take(&completion_sem, TEST_WAIT), 0,
		      "worker did not signal completion after sleeping");

	zassert_true(worker_finished_ms - sleep_started_ms >= 100,
		     "worker resumed before the sleep timeout");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "unexpected duplicate completion signal");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
