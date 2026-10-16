#include <errno.h>
#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 40
#define WAIT_MS 500

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem sleep_entered;
static struct k_sem completed;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&sleep_entered);
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	zassert_equal(k_sem_init(&sleep_entered, 0, 1), 0);
	zassert_equal(k_sem_init(&completed, 0, 1), 0);

	zassert_not_null(k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), worker,
		NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT));

	/* This immediate signal is distinct from the completion event. */
	zassert_equal(k_sem_take(&sleep_entered, K_MSEC(WAIT_MS)), 0);
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY);
	zassert_equal(k_sem_take(&completed, K_MSEC(WAIT_MS)), 0);
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS);
	zassert_equal(k_thread_join(&worker_thread, K_MSEC(WAIT_MS)), 0);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
