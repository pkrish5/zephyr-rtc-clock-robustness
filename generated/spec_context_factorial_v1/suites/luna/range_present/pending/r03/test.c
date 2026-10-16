#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <string.h>

#define TIMER_DELAY K_MSEC(500)
#define WAIT_TIMEOUT K_SECONDS(2)

K_SEM_DEFINE(worker_ready, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);
K_TIMER_DEFINE(test_timer, NULL, NULL);

static struct k_thread worker_thread;
K_THREAD_STACK_DEFINE(worker_stack, 1024);
static volatile uint32_t received_status;

static void timer_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&worker_ready);
	received_status = k_timer_status_sync(&test_timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_interrupt_delivery, test_blocked_thread_receives_timer_expiry)
{
	received_status = 0;
	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			timer_worker, NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&worker_ready, WAIT_TIMEOUT), "worker did not start");

	/* Wait for the worker to enter k_timer_status_sync's pending state. */
	int64_t deadline = k_uptime_get() + 400;
	bool pending = false;
	while (k_uptime_get() < deadline) {
		if (strstr(k_thread_state_str(&worker_thread), "pending") != NULL) {
			pending = true;
			break;
		}
		k_sleep(K_MSEC(1));
	}
	zassert_true(pending, "worker was not pending before timer expiry");
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "completion occurred before timer expiry");

	zassert_ok(k_sem_take(&worker_done, WAIT_TIMEOUT), "timer did not complete worker");
	zassert_equal(received_status, 1, "expected exactly one timer expiration");
}

ZTEST_SUITE(timer_interrupt_delivery, NULL, NULL, NULL, NULL, NULL);
