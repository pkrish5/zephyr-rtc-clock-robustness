#include <errno.h>
#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
K_SEM_DEFINE(start_gate, 0, 1);
K_SEM_DEFINE(entered_wait, 0, 1);
K_SEM_DEFINE(completed, 0, 1);
static uint32_t received_expirations;

static void timer_worker(void *a, void *b, void *c)
{
	(void)a;
	(void)b;
	(void)c;

	k_sem_take(&start_gate, K_FOREVER);
	k_sem_give(&entered_wait);
	received_expirations = k_timer_status_sync(&timer);
	k_sem_give(&completed);
}

ZTEST(timer_delivery, test_one_shot_expiry_wakes_worker)
{
	k_timer_init(&timer, NULL, NULL);
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	k_timer_start(&timer, K_MSEC(1000), K_NO_WAIT);
	k_sem_give(&start_gate);
	zassert_ok(k_sem_take(&entered_wait, K_SECONDS(2)));

	/* Allow the worker to enter k_timer_status_sync before expiry. */
	k_sleep(K_MSEC(20));
	zassert_true(k_timer_remaining_get(&timer) > 0);
	zassert_equal(k_thread_join(&worker_thread, K_NO_WAIT), -EBUSY);
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY);

	zassert_ok(k_sem_take(&completed, K_SECONDS(5)));
	zassert_equal(received_expirations, 1U);
	zassert_ok(k_thread_join(&worker_thread, K_NO_WAIT));
}

ZTEST_SUITE(timer_delivery, NULL, NULL, NULL, NULL, NULL);