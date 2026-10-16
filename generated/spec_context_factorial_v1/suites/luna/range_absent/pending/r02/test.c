#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_SEM_DEFINE(completion, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static struct k_timer test_timer;
static volatile bool worker_entered_wait;
static volatile uint32_t timer_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	worker_entered_wait = true;
	timer_status = k_timer_status_sync(&test_timer);
	k_sem_give(&completion);
}

ZTEST(timer_interrupt, test_blocked_thread_receives_timer_expiry)
{
	worker_entered_wait = false;
	timer_status = 0U;
	k_sem_reset(&completion);
	k_timer_init(&test_timer, NULL, NULL);

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			timer_worker, NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);

	/* Wait until the worker has reached the timer wait, then check it remains pending. */
	while (!worker_entered_wait) {
		k_yield();
	}
	zassert_equal(k_sem_take(&completion, K_NO_WAIT), -EBUSY,
		      "worker completed before timer was started");
	zassert_equal(k_thread_state_get(&worker_thread) & _THREAD_PENDING,
		      _THREAD_PENDING, "worker was not blocked awaiting the timer");

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);

	zassert_ok(k_sem_take(&completion, K_SECONDS(2)), "timer completion was not signaled");
	zassert_equal(timer_status, 1U, "expected exactly one timer expiration");
	zassert_equal(k_timer_status_get(&test_timer), 0U,
		      "timer expiration status was not consumed by the worker");

	k_thread_join(&worker_thread, K_SECONDS(1));
	k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
