#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define SLEEP_MS 50
#define WAIT_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem ready_sem;
static struct k_sem done_sem;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* This immediate signal is deliberately separate from completion. */
	k_sem_give(&ready_sem);
	sleep_start_ms = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&done_sem);
}

ZTEST(timer_sleep, test_interrupt_driven_wakeup)
{
	k_tid_t tid;
	int immediate_result;
	int completion_result;
	int join_result;

	zassert_equal(k_sem_init(&ready_sem, 0, 1), 0,
		      "Failed to initialize readiness semaphore");
	zassert_equal(k_sem_init(&done_sem, 0, 1), 0,
		      "Failed to initialize completion semaphore");

	/*
	 * On this single CPU, the cooperative worker cannot be preempted
	 * by the test between signaling readiness and blocking in k_sleep().
	 */
	tid = k_thread_create(&worker_thread, worker_stack,
			      K_THREAD_STACK_SIZEOF(worker_stack), worker,
			      NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready_sem, K_MSEC(WAIT_MS)), 0,
		      "Worker did not signal readiness");

	/* Readiness must not masquerade as completion of the timed sleep. */
	immediate_result = k_sem_take(&done_sem, K_NO_WAIT);
	completion_result = k_sem_take(&done_sem, K_MSEC(WAIT_MS));
	join_result = k_thread_join(tid, K_MSEC(WAIT_MS));

	zassert_true(immediate_result != 0,
		     "Worker completed immediately instead of remaining asleep");
	zassert_equal(completion_result, 0,
		      "No completion event arrived after the sleep timeout");
	zassert_equal(join_result, 0, "Worker did not exit");
	zassert_true(sleep_end_ms - sleep_start_ms >= SLEEP_MS,
		     "Worker resumed before the requested sleep elapsed");
	zassert_true(k_sem_take(&done_sem, K_NO_WAIT) != 0,
		     "Unexpected extra completion event");
}

ZTEST_SUITE(timer_sleep, NULL, NULL, NULL, NULL, NULL);
