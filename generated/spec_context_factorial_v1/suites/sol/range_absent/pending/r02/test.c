#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(worker_entered, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);

static struct k_thread worker_thread;
static struct k_timer timer;
static uint32_t received_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&worker_entered);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_sync_suite, test_one_shot_expiry_wakes_worker)
{
	k_timer_init(&timer, NULL, NULL);
	k_timer_start(&timer, K_MSEC(500), K_NO_WAIT);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&worker_entered, K_MSEC(100)));
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "timer expired before the pending check");
	zassert_equal(k_sem_take(&worker_done, K_MSEC(20)), -EAGAIN,
		      "worker completed before timer expiry");
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "timer expired during the pending check");

	zassert_ok(k_sem_take(&worker_done, K_MSEC(1000)));
	zassert_equal(received_status, 1U,
		      "worker did not receive exactly one timer expiry");
}

ZTEST_SUITE(timer_sync_suite, NULL, NULL, NULL, NULL, NULL);
