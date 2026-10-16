#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define TEST_TIMEOUT K_MSEC(1000)

static struct k_timer test_timer;
static struct k_sem worker_started;
static struct k_sem worker_done;
static atomic_t received_status;
static atomic_t worker_error;
static struct k_thread worker_thread;
K_THREAD_STACK_DEFINE(worker_stack, 1024);

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&worker_started);
	uint32_t status = k_timer_status_sync(&test_timer);
	atomic_set(&received_status, (atomic_val_t)status);
	k_sem_give(&worker_done);
}

ZTEST(timer_interrupt_path, test_blocked_thread_receives_timer_expiry)
{
	k_sem_init(&worker_started, 0, 1);
	k_sem_init(&worker_done, 0, 1);
	atomic_set(&received_status, 0);
	atomic_set(&worker_error, 0);
	k_timer_init(&test_timer, NULL, NULL);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);
	k_thread_name_set(&worker_thread, "timer_worker");

	zassert_ok(k_sem_take(&worker_started, TEST_TIMEOUT),
		   "worker did not start");
	/* Let the worker enter status_sync before starting the one-shot timer. */
	k_sleep(K_MSEC(10));
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EAGAIN,
		      "worker completed before timer expiry");

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	zassert_ok(k_sem_take(&worker_done, TEST_TIMEOUT),
		   "timer expiry did not complete the worker");
	zassert_equal(atomic_get(&received_status), 1,
		      "worker did not receive exactly one timer expiration");
	zassert_equal(atomic_get(&worker_error), 0, "worker reported an error");
	k_thread_join(&worker_thread, TEST_TIMEOUT);
	k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
