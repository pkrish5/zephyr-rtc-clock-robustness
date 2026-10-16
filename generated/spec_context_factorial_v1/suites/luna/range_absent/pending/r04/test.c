#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_TIMER_DEFINE(test_timer, NULL, NULL);
K_SEM_DEFINE(worker_done, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static atomic_t worker_started;
static atomic_t worker_status;

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	atomic_set(&worker_started, 1);
	int status = k_timer_status_sync(&test_timer);
	atomic_set(&worker_status, status);
	k_sem_give(&worker_done);
}

ZTEST(timer_interrupt_path, test_one_shot_expiration_wakes_blocked_worker)
{
	atomic_clear(&worker_started);
	atomic_set(&worker_status, -1);
	k_sem_reset(&worker_done);
	k_timer_stop(&test_timer);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			worker_timer, NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);
	/* Worker signals immediately before waiting; let it reach the timer wait. */
	while (atomic_get(&worker_started) == 0) {
		k_yield();
	}
	k_sleep(K_MSEC(10));
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "worker completed before timer was started");

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	zassert_ok(k_sem_take(&worker_done, K_SECONDS(2)),
		   "timer expiry did not complete worker");
	zassert_equal(atomic_get(&worker_status), 1,
		      "worker did not observe one timer expiration");
	zassert_equal(k_timer_status_get(&test_timer), 0,
		      "timer expiration status was not consumed");
	k_thread_join(&worker_thread, K_SECONDS(1));
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
