#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem worker_ready;
static struct k_sem worker_done;
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

ZTEST(timer_interrupt, test_one_shot_expiry_wakes_worker)
{
	k_timer_init(&timer, NULL, NULL);
	k_sem_init(&worker_ready, 0, 1);
	k_sem_init(&worker_done, 0, 1);
	received_status = 0;

	k_timer_start(&timer, K_MSEC(200), K_NO_WAIT);
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&worker_ready, K_MSEC(100)));
	k_sleep(K_MSEC(10));
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "timer expired before pending check");
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "worker completed before timer expiry");
	zassert_equal(k_thread_join(&worker_thread, K_NO_WAIT), -EBUSY,
		      "worker was not pending");

	zassert_ok(k_sem_take(&worker_done, K_MSEC(1000)));
	zassert_ok(k_thread_join(&worker_thread, K_MSEC(100)));
	zassert_equal(received_status, 1U,
		      "worker did not receive exactly one timer expiration");
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
