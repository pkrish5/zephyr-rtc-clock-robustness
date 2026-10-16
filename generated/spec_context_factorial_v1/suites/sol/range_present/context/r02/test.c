#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_STACK_SIZE 1024
#define SLEEP_MS 100

K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);

static struct k_thread worker_thread;
static struct k_sem sleep_started;
static struct k_sem completion;
static struct k_sem unrelated;
static int64_t sleep_start_ms;
static int64_t wake_ms;

static void worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&sleep_started);
	sleep_start_ms = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	wake_ms = k_uptime_get();
	k_sem_give(&completion);
}

ZTEST(timer_sleep, test_worker_wakes_after_timeout)
{
	zassert_ok(k_sem_init(&sleep_started, 0, 1));
	zassert_ok(k_sem_init(&completion, 0, 1));
	zassert_ok(k_sem_init(&unrelated, 0, 1));

	zassert_not_null(k_thread_create(&worker_thread, worker_stack,
					 K_THREAD_STACK_SIZEOF(worker_stack),
					 worker, NULL, NULL, NULL,
					 K_PRIO_PREEMPT(5), 0, K_NO_WAIT));

	zassert_ok(k_sem_take(&sleep_started, K_SECONDS(1)));

	/* An immediate, unrelated signal must not count as completion. */
	k_sem_give(&unrelated);
	zassert_ok(k_sem_take(&unrelated, K_NO_WAIT));
	zassert_not_equal(k_sem_take(&completion, K_MSEC(10)), 0,
			  "worker completed during its timed sleep");

	zassert_ok(k_sem_take(&completion, K_SECONDS(2)),
		   "worker did not report completion");
	zassert_true(wake_ms - sleep_start_ms >= SLEEP_MS,
		     "worker resumed before the sleep timeout");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
