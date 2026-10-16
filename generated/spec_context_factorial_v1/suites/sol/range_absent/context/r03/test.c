#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 50

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem started;
static struct k_sem finished;
static int64_t sleep_start_ms;
static int64_t wake_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_start_ms = k_uptime_get();
	k_sem_give(&started);
	k_sleep(K_MSEC(SLEEP_MS));
	wake_ms = k_uptime_get();
	k_sem_give(&finished);
}

ZTEST(timer_sleep, test_thread_wakes_after_timeout)
{
	k_sem_init(&started, 0, 1);
	k_sem_init(&finished, 0, 1);

	zassert_not_null(k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), worker,
		NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT));

	/* The immediate start signal must not count as completion. */
	zassert_ok(k_sem_take(&started, K_MSEC(200)));
	zassert_not_equal(k_sem_take(&finished, K_NO_WAIT), 0);

	zassert_ok(k_sem_take(&finished, K_MSEC(500)));
	zassert_true(wake_ms - sleep_start_ms >= SLEEP_MS);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
