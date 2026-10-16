#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5
#define TIMER_DELAY K_MSEC(100)

K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static struct k_timer test_timer;
static struct k_sem completion_sem;
static atomic_t worker_pending;
static atomic_t worker_status;

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	atomic_set(&worker_pending, 1);
	atomic_set(&worker_status, (atomic_val_t)k_timer_status_sync(&test_timer));
	k_sem_give(&completion_sem);
}

ZTEST(timer_interrupt_path, test_worker_receives_one_shot_expiration)
{
	k_sem_init(&completion_sem, 0, 1);
	atomic_clear(&worker_pending);
	atomic_set(&worker_status, -1);
	k_timer_init(&test_timer, NULL, NULL);

	k_tid_t worker = k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
		NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);
	zassert_not_null(worker, "worker thread creation failed");

	/* Wait until the worker is about to block on the timer status. */
	while (atomic_get(&worker_pending) == 0) {
		k_yield();
	}
	zassert_equal(k_timer_status_get(&test_timer), 0,
		"timer must not have expired before it is started");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
		"worker completed before timer expiry");

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	zassert_equal(k_sem_take(&completion_sem, K_SECONDS(2)), 0,
		"timer expiration did not complete worker");
	zassert_equal(atomic_get(&worker_status), 1,
		"worker did not receive exactly one timer expiration");
	zassert_equal(k_timer_status_get(&test_timer), 0,
		"timer expiration event was not consumed by worker");

	k_timer_stop(&test_timer);
	k_thread_join(worker, K_SECONDS(1));
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
