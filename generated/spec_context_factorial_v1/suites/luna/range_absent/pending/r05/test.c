#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)

K_TIMER_DEFINE(test_timer, NULL, NULL);
K_SEM_DEFINE(worker_started, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);
static volatile uint32_t received_status;

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&worker_started);
	received_status = k_timer_status_sync(&test_timer);
	k_sem_give(&worker_done);
}

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;

ZTEST(timer_interrupt, test_blocked_thread_receives_timer_expiration)
{
	received_status = UINT32_MAX;
	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			timer_worker, NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&worker_started, K_SECONDS(1)), 0,
		      "worker did not start");
	/* The timer is still running, so status_sync must have blocked the worker. */
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EAGAIN,
		      "worker completed before timer expiry");
	zassert_equal(k_sem_take(&worker_done, K_SECONDS(2)), 0,
		      "timer expiry did not complete worker");
	zassert_equal(received_status, 1U, "expected one timer expiration");

	k_thread_join(&worker_thread, K_SECONDS(1));
	k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
