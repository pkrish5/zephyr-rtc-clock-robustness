#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define TEST_WAIT K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completion_sem;
static struct k_sem unrelated_sem;
static int64_t worker_start_ms;
static int64_t worker_done_ms;

static void worker_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	worker_start_ms = k_uptime_get();
	k_sleep(WORKER_SLEEP);
	worker_done_ms = k_uptime_get();
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep, test_thread_sleep_wakeup)
{
	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);
	worker_start_ms = -1;
	worker_done_ms = -1;

	/* An unrelated event must not be mistaken for worker completion. */
	k_sem_give(&unrelated_sem);

	(void)k_thread_create(&worker_thread, worker_stack,
			      K_THREAD_STACK_SIZEOF(worker_stack),
			      worker_entry, NULL, NULL, NULL,
			      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&unrelated_sem, K_NO_WAIT), 0,
		      "unrelated signal should be available");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker completed immediately");

	zassert_equal(k_sem_take(&completion_sem, TEST_WAIT), 0,
		      "worker completion event timed out");
	zassert_true(worker_start_ms >= 0, "worker did not enter sleep");
	zassert_true(worker_done_ms - worker_start_ms >= 80,
		     "worker resumed before the sleep timeout");

	k_thread_join(&worker_thread, TEST_WAIT);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
