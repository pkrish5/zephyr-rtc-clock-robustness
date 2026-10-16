#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem done;
static uint32_t received_status;

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, K_MSEC(250), K_NO_WAIT);
	k_sem_give(&ready);
	/* Cooperative execution continues until status_sync blocks. */
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&done);
}

ZTEST(timer_wait, test_one_shot_interrupt_wakeup)
{
	k_timer_init(&timer, NULL, NULL);
	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	received_status = 0;

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), worker,
		NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	int ready_rc = k_sem_take(&ready, K_SECONDS(1));
	/*
	 * On this single CPU, the cooperative worker cannot yield execution
	 * after giving ready until it blocks in k_timer_status_sync().
	 * Remaining time also establishes that expiry has not yet occurred.
	 */
	k_ticks_t remaining = k_timer_remaining_ticks(&timer);
	int early_rc = k_sem_take(&done, K_NO_WAIT);
	int completion_rc = early_rc;

	if (early_rc != 0) {
		completion_rc = k_sem_take(&done, K_SECONDS(1));
	}
	int join_rc = k_thread_join(tid, K_SECONDS(1));

	/* Clean up before assertions, including on a failed wakeup. */
	if (join_rc != 0) {
		k_thread_abort(tid);
	}
	k_timer_stop(&timer);

	zassert_equal(ready_rc, 0, "Worker did not reach timer wait");
	zassert_true(remaining > 0, "Timer expired before pending check");
	zassert_true(early_rc != 0, "Worker completed before expiry check");
	zassert_equal(completion_rc, 0, "Timer completion was lost");
	zassert_equal(join_rc, 0, "Worker did not exit");
	zassert_equal(received_status, 1, "Expected one timer expiration");
	zassert_equal(k_timer_status_get(&timer), 0,
		      "Synchronized expiration was not consumed");
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
