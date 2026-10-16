#include <zephyr/ztest.h>
#include <zephyr/kernel.h>

#define TIMER_DELAY K_MSEC(100)

static struct k_timer test_timer;
static struct k_sem completion;
static struct k_thread worker_thread;
K_THREAD_STACK_DEFINE(worker_stack, 1024);

static void timer_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	/* This blocks until the kernel timer expiry records a status. */
	uint32_t status = k_timer_status_sync(&test_timer);
	zassert_equal(status, 1U, "expected exactly one timer expiration");
	k_sem_give(&completion);
}

ZTEST(timer_expiry, test_blocked_thread_receives_timer_expiry)
{
	k_sem_init(&completion, 0, 1);
	k_timer_init(&test_timer, NULL, NULL);

	k_tid_t worker = k_thread_create(&worker_thread, worker_stack,
					 K_THREAD_STACK_SIZEOF(worker_stack),
					 timer_worker, NULL, NULL, NULL,
					 K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Ensure the worker has reached the status wait before starting the timer. */
	zassert_equal(k_sem_take(&completion, K_NO_WAIT), -EBUSY,
		      "worker completed before timer was started");
	k_thread_suspend(worker);
	k_thread_resume(worker);
	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);

	/* Wait for completion with a generous scheduling margin. */
	zassert_ok(k_sem_take(&completion, K_SECONDS(2)),
		   "timer expiration did not complete worker");
	zassert_equal(k_timer_status_get(&test_timer), 0U,
		      "expiration status should have been consumed by worker");

	k_timer_stop(&test_timer);
	k_thread_abort(worker);
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
