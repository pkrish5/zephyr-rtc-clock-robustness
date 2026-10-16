#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <errno.h>

#define TIMER_DELAY K_MSEC(500)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem completed;
static unsigned int expiry_count;

static void timer_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, TIMER_DELAY, K_NO_WAIT);
	k_sem_give(&ready);
	expiry_count = k_timer_status_sync(&timer);
	k_sem_give(&completed);
}

ZTEST(timer_wait, test_one_shot_expiry_wakes_worker)
{
	expiry_count = 0;
	k_timer_init(&timer, NULL, NULL);
	k_sem_init(&ready, 0, 1);
	k_sem_init(&completed, 0, 1);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready, K_MSEC(100)), 0);
	k_sleep(K_MSEC(20));
	zassert_true(k_timer_remaining_get(&timer) > 0);
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY);

	zassert_equal(k_sem_take(&completed, K_SECONDS(2)), 0);
	zassert_equal(expiry_count, 1U);
	zassert_equal(k_thread_join(&worker_thread, K_MSEC(100)), 0);
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
