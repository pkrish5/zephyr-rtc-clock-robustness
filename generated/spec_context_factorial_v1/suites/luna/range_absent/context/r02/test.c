#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define TEST_TIMEOUT K_SECONDS(2)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);

static struct k_sem completion_sem;
static struct k_sem unrelated_sem;
static struct k_thread worker_thread;
static int64_t worker_start_ms;
static int64_t worker_done_ms;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	worker_start_ms = k_uptime_get();
	k_sleep(WORKER_SLEEP);
	worker_done_ms = k_uptime_get();
	k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timed_sleep)
{
	const int64_t minimum_elapsed_ms = 80;
	int64_t elapsed_ms;

	k_sem_init(&completion_sem, 0, 1);
	k_sem_init(&unrelated_sem, 0, 1);
	worker_start_ms = -1;
	worker_done_ms = -1;

	/* An unrelated event must not be mistaken for worker completion. */
	k_sem_give(&unrelated_sem);
	zassert_equal(k_sem_take(&unrelated_sem, K_NO_WAIT), 0,
		      "unrelated event was not available");
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker completion arrived before the worker was started");

	k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			sleep_worker, NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);

	/* The worker cannot finish its timed sleep before this check. */
	k_sleep(K_MSEC(20));
	zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EAGAIN,
		      "worker completed immediately instead of sleeping");
	zassert_true(worker_start_ms >= 0, "worker did not enter its sleep path");

	zassert_equal(k_sem_take(&completion_sem, TEST_TIMEOUT), 0,
		      "worker completion did not arrive before the timeout");
	elapsed_ms = worker_done_ms - worker_start_ms;
	zassert_true(elapsed_ms >= minimum_elapsed_ms,
		     "worker resumed too early: elapsed %lld ms",
		     (long long)elapsed_ms);
	zassert_true(worker_done_ms >= worker_start_ms,
		     "worker timestamps were not ordered");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
