#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)

static struct k_timer test_timer;
static struct k_sem completion_sem;
static struct k_thread worker_thread;
K_THREAD_STACK_DEFINE(worker_stack, 1024);

static volatile uint32_t received_status;
static volatile bool worker_started;
static volatile bool timer_received;

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	worker_started = true;
	received_status = k_timer_status_sync(&test_timer);
	timer_received = true;
	k_sem_give(&completion_sem);
}

ZTEST(timer_blocked_expiry, test_timer_expiry_unblocks_worker)
{
	k_sem_init(&completion_sem, 0, 1);
	worker_started = false;
	timer_received = false;
	received_status = 0;
	k_timer_init(&test_timer, NULL, NULL);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			 timer_worker, NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	k_thread_name_set(&worker_thread, "timer_worker");

	/* Wait for the worker to enter its wait path before starting the timer. */
	while (!worker_started) {
		k_yield();
	}
	k_sleep(K_MSEC(10));
	zassert_equal(k_timer_status_get(&test_timer), 0U,
		      "timer must not have expired before it is started");
	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);

	zassert_equal(k_sem_take(&completion_sem, K_MSEC(1000)), 0,
		      "worker did not signal completion after timer expiry");
	zassert_true(timer_received, "worker did not receive the timer event");
	zassert_equal(received_status, 1U, "expected one timer expiration");
	zassert_equal(k_timer_status_get(&test_timer), 0U,
		      "status_sync should have consumed the expiration");

	k_thread_join(&worker_thread, K_MSEC(1000));
}

ZTEST_SUITE(timer_blocked_expiry, NULL, NULL, NULL, NULL, NULL);
