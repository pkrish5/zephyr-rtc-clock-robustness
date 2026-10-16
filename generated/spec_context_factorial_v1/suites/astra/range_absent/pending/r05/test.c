#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

static struct k_timer timer;
static struct k_sem entered;
static struct k_sem completed;
static struct k_thread worker_thread;
static K_THREAD_STACK_DEFINE(worker_stack, 1024);
static uint32_t received_status;

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&entered);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&completed);
}

ZTEST(timer_wait, test_one_shot_wakes_blocked_worker)
{
	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);
	k_timer_init(&timer, NULL, NULL);
	received_status = 0;

	/* Start first: status_sync does not wait on a stopped timer. */
	k_timer_start(&timer, K_MSEC(1000), K_NO_WAIT);
	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				    K_THREAD_STACK_SIZEOF(worker_stack),
				    worker, NULL, NULL, NULL,
				    K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&entered, K_MSEC(500)), 0,
		      "Worker did not reach the timer wait");

	/*
	 * On this single CPU, the highest-priority cooperative worker
	 * cannot yield to this test between giving entered and blocking
	 * in status_sync. Thus resuming here, with the timer still pending
	 * and no completion, proves that the worker is blocked.
	 */
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0,
			 "Worker completed before the pending check");
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "Timer expired before the pending check");

	/* The kernel timer interrupt must release the status_sync wait. */
	zassert_equal(k_sem_take(&completed, K_MSEC(2000)), 0,
		      "Timer expiry did not produce completion");
	zassert_equal(received_status, 1U,
		      "Expected exactly one timer expiration");
	zassert_equal(k_timer_status_get(&timer), 0U,
		      "status_sync did not consume the expiration");
	zassert_equal(k_thread_join(tid, K_MSEC(500)), 0,
		      "Worker did not exit");
	k_timer_stop(&timer);
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
