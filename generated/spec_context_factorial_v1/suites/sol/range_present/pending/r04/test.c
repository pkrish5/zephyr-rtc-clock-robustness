#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(worker_ready, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);

static struct k_thread worker_thread;
static struct k_timer timer;
static uint32_t received_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&worker_ready);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_expiry, test_blocked_worker_receives_expiry)
{
	k_timer_init(&timer, NULL, NULL);
	received_status = 0U;

	/* The cooperative worker runs through status_sync before this thread resumes. */
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&worker_ready, K_MSEC(1000)), 0);
	zassert_not_equal(k_sem_take(&worker_done, K_NO_WAIT), 0,
			  "worker completed before timer start");
	zassert_not_equal(k_thread_join(&worker_thread, K_NO_WAIT), 0,
			  "worker was not blocked");

	k_timer_start(&timer, K_MSEC(100), K_NO_WAIT);
	zassert_equal(k_sem_take(&worker_done, K_MSEC(2000)), 0,
		      "timer expiry did not complete the worker");
	zassert_equal(received_status, 1U,
		      "worker did not receive the one-shot expiry");
	zassert_equal(k_thread_join(&worker_thread, K_MSEC(1000)), 0);
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
