#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define WORKER_SLEEP K_MSEC(100)
#define TEST_TIMEOUT K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem completed;
static struct k_sem unrelated;
static int64_t worker_started_at;
static int64_t worker_finished_at;

static void sleep_worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	worker_started_at = k_uptime_get();
	k_sleep(WORKER_SLEEP);
	worker_finished_at = k_uptime_get();
	k_sem_give(&completed);
}

ZTEST(timer_sleep_wakeup, test_worker_wakes_after_timed_sleep)
{
	k_sem_init(&completed, 0, 1);
	k_sem_init(&unrelated, 0, 1);
	worker_started_at = 0;
	worker_finished_at = 0;

	/* This immediate signal must not be mistaken for worker completion. */
	k_sem_give(&unrelated);
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "worker completion must not be available immediately");
	zassert_ok(k_sem_take(&unrelated, K_NO_WAIT),
		   "unrelated immediate signal should be available");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "unrelated signal must not count as worker completion");

	zassert_ok(k_sem_take(&completed, TEST_TIMEOUT),
		   "worker should complete after its timed sleep");
	zassert_true(worker_finished_at - worker_started_at >= 80,
		     "worker resumed too early: elapsed %lld ms",
		     (long long)(worker_finished_at - worker_started_at));
	zassert_true(worker_finished_at - worker_started_at < 1000,
		     "worker sleep exceeded its bounded interval");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "completion event should be delivered only once");
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
