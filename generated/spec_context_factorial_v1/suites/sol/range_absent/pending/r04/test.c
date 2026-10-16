#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready_sem;
static struct k_sem done_sem;
static uint32_t received_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&ready_sem);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&done_sem);
}

ZTEST(timer_interrupt_path, test_one_shot_wakes_blocked_thread)
{
	k_sem_init(&ready_sem, 0, 1);
	k_sem_init(&done_sem, 0, 1);
	k_timer_init(&timer, NULL, NULL);
	received_status = 0;

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&ready_sem, K_MSEC(100)));
	k_sleep(K_MSEC(10));
	/* The worker has run and is waiting for an expiry. */
	zassert_not_equal(k_thread_join(&worker_thread, K_NO_WAIT), 0);
	zassert_not_equal(k_sem_take(&done_sem, K_NO_WAIT), 0);

	k_timer_start(&timer, K_MSEC(50), K_NO_WAIT);
	zassert_ok(k_sem_take(&done_sem, K_MSEC(200)));
	zassert_equal(received_status, 1);
	zassert_ok(k_thread_join(&worker_thread, K_NO_WAIT));
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
