#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 100

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_sem started;
static struct k_sem completed;
static struct k_sem unrelated;
static int32_t sleep_remaining;
static int64_t sleep_elapsed_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	int64_t start_ms = k_uptime_get();

	k_sem_give(&started);
	sleep_remaining = k_sleep(K_MSEC(SLEEP_MS));
	sleep_elapsed_ms = k_uptime_get() - start_ms;
	k_sem_give(&completed);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	zassert_equal(k_sem_init(&started, 0, 1), 0);
	zassert_equal(k_sem_init(&completed, 0, 1), 0);
	zassert_equal(k_sem_init(&unrelated, 0, 1), 0);

	zassert_not_null(k_thread_create(&worker_thread, worker_stack,
					 K_THREAD_STACK_SIZEOF(worker_stack),
					 worker, NULL, NULL, NULL,
					 K_PRIO_PREEMPT(0), 0, K_NO_WAIT));

	zassert_equal(k_sem_take(&started, K_MSEC(1000)), 0);
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);

	k_sem_give(&unrelated);
	zassert_equal(k_sem_take(&unrelated, K_NO_WAIT), 0);
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);

	zassert_equal(k_sem_take(&completed, K_MSEC(1000)), 0);
	zassert_equal(sleep_remaining, 0);
	zassert_true(sleep_elapsed_ms >= SLEEP_MS);
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);