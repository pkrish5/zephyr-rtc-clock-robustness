#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <string.h>

#define TIMER_DELAY K_MSEC(1000)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_SEM_DEFINE(worker_ready, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);
K_TIMER_DEFINE(test_timer, NULL, NULL);
K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static uint32_t received_expirations;

static void timer_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* Tell the test we are about to wait; status_sync blocks until expiry. */
	k_sem_give(&worker_ready);
	received_expirations = k_timer_status_sync(&test_timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_interrupt_path, test_blocked_thread_receives_one_shot_expiry)
{
	int64_t start_ms;
	int64_t expiry_ms;
	bool observed_pending = false;

	received_expirations = 0;
	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
	start_ms = k_uptime_get();
	expiry_ms = start_ms + 1000;

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			 timer_worker, NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);
	zassert_equal(k_sem_take(&worker_ready, K_SECONDS(1)), 0,
		      "worker did not reach the timer wait");

	/* Confirm the worker is pending before the one-shot timer can expire. */
	while (k_uptime_get() < expiry_ms) {
		if (strcmp(k_thread_state_str(&worker_thread), "pending") == 0) {
			observed_pending = true;
			break;
		}
		k_yield();
	}
	zassert_true(observed_pending, "worker was not observed pending before expiry");

	zassert_equal(k_sem_take(&worker_done, K_SECONDS(2)), 0,
		      "timer expiry did not complete the worker");
	zassert_equal(received_expirations, 1U,
		      "expected exactly one timer expiration status");
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
