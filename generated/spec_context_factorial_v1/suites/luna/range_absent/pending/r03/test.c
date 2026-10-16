#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define THREAD_STACK_SIZE 1024
#define THREAD_PRIORITY 5

K_TIMER_DEFINE(test_timer, NULL, NULL);
K_SEM_DEFINE(worker_done, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, THREAD_STACK_SIZE);

static struct k_thread worker_thread;
static atomic_t worker_started;
static atomic_t worker_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	atomic_set(&worker_started, 1);
	atomic_set(&worker_status, (atomic_val_t)k_timer_status_sync(&test_timer));
	k_sem_give(&worker_done);
}

ZTEST(timer_interrupt, test_blocked_thread_receives_timer_expiry)
{
	atomic_clear(&worker_started);
	atomic_set(&worker_status, -1);
	k_sem_reset(&worker_done);

	k_timer_init(&test_timer, NULL, NULL);
	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			timer_worker, NULL, NULL, NULL, THREAD_PRIORITY, 0, K_NO_WAIT);
	k_thread_name_set(&worker_thread, "timer_worker");

	/* Wait until the worker enters status_sync, then verify it is still blocked. */
	K_ASSERT_OK(k_sem_take(&worker_done, K_NO_WAIT) == 0 ? -1 : 0);
	K_ASSERT_TRUE(atomic_get(&worker_started) == 1);
	K_ASSERT_EQUAL(k_timer_status_get(&test_timer), 0);
	K_ASSERT_EQUAL(k_thread_state_str(&worker_thread)[0], 'p');

	k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);

	K_ASSERT_OK(k_sem_take(&worker_done, K_SECONDS(2)));
	K_ASSERT_EQUAL(atomic_get(&worker_status), 1);
	K_ASSERT_EQUAL(k_timer_status_get(&test_timer), 0);

	k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
