#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_TIMER_DEFINE(test_timer, NULL);
K_SEM_DEFINE(worker_done, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static atomic_t worker_pending;
static uint32_t received_status;

static void timer_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	atomic_set(&worker_pending, 1);
	received_status = k_timer_status_sync(&test_timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_blocking, test_timer_expiry_wakes_blocked_worker)
{
	atomic_clear(&worker_pending);
	received_status = 0U;
	k_sem_reset(&worker_done);
	k_timer_stop(&test_timer);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			timer_worker, NULL, NULL, NULL,
			WORKER_PRIORITY, 0, K_NO_WAIT);
	k_thread_name_set(&worker_thread, "timer_worker");

	/* Wait until the worker is about to block in status_sync. */
	zassert_ok(k_sem_take(&worker_done, K_NO_WAIT),
		   "completion semaphore unexpectedly available");
	while (atomic_get(&worker_pending) == 0) {
		k_yield();
	}
	k_sleep(K_MSEC(10));
	zassert_equal(k_thread_state_str(&worker_thread)[0], 'p',
		      "worker should be pending before timer expiry");

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	zassert_ok(k_sem_take(&worker_done, K_SECONDS(1)),
		   "worker did not complete after timer expiry");
	zassert_equal(received_status, 1U,
		      "worker should receive one timer expiration");
	zassert_equal(k_timer_status_get(&test_timer), 0U,
		      "timer expiration status should be consumed");

	k_thread_join(&worker_thread, K_SECONDS(1));
	k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_blocking, NULL, NULL, NULL, NULL, NULL);
