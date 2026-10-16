#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP_MS 50
#define TEST_TIMEOUT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem worker_done;
static struct k_sem worker_started;
static struct k_sem unrelated_signal;

static void sleep_worker(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&worker_started);
	k_sleep(K_MSEC(WORKER_SLEEP_MS));
	k_sem_give(&worker_done);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timed_sleep)
{
	int64_t start;
	int64_t elapsed;

	k_sem_init(&worker_done, 0, 1);
	k_sem_init(&worker_started, 0, 1);
	k_sem_init(&unrelated_signal, 0, 1);

	/* A distinct event must not be mistaken for worker completion. */
	k_sem_give(&unrelated_signal);
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "worker completion was signaled before the worker ran");
	zassert_equal(k_sem_take(&unrelated_signal, K_NO_WAIT), 0,
		      "unrelated signal was not available");
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "unrelated signal was mistaken for completion");

	start = k_uptime_get();
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&worker_started, K_MSEC(TEST_TIMEOUT_MS)), 0,
		      "worker did not start");
	zassert_equal(k_sem_take(&worker_done, K_NO_WAIT), -EBUSY,
		      "worker completed immediately instead of entering timed sleep");

	zassert_equal(k_sem_take(&worker_done, K_MSEC(TEST_TIMEOUT_MS)), 0,
		      "worker did not signal completion after sleeping");
	elapsed = k_uptime_get() - start;
	zassert_true(elapsed >= WORKER_SLEEP_MS,
		     "completion arrived before the sleep timeout: %lld ms",
		     (long long)elapsed);
	zassert_true(elapsed < TEST_TIMEOUT_MS,
		     "completion arrived outside the bounded timeout: %lld ms",
		     (long long)elapsed);
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
