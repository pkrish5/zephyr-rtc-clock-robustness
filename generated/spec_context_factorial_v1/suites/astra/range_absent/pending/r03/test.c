#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

#define WORKER_STACK_SIZE 1024

static K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem completed;
static atomic_t phase;
static atomic_t expiry_in_isr;
static uint32_t received_status;

static void timer_expired(struct k_timer *unused)
{
	ARG_UNUSED(unused);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : -1);
}

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	atomic_set(&phase, 1);
	received_status = k_timer_status_sync(&timer);
	atomic_set(&phase, 2);
	k_sem_give(&completed);
}

ZTEST(timer_wait, test_interrupt_expiry_wakes_pending_worker)
{
	k_tid_t self = k_current_get();
	int original_priority = k_thread_priority_get(self);
	int pending_phase;
	int early_completion;
	int early_expiry;
	uint32_t remaining;
	int completion_result;
	int join_result;

	k_sem_init(&completed, 0, 1);
	k_timer_init(&timer, timer_expired, NULL);
	atomic_set(&phase, 0);
	atomic_set(&expiry_in_isr, 0);
	received_status = 0;

	/* The cooperative worker outranks this preemptible test thread. */
	k_thread_priority_set(self, K_PRIO_PREEMPT(0));
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_FOREVER);

	k_timer_start(&timer, K_MSEC(500), K_NO_WAIT);
	k_thread_start(&worker_thread);

	/*
	 * On this single CPU, execution returns here only after the
	 * higher-priority worker blocks or finishes. Phase 1, no completion,
	 * and an unexpired timer therefore establish that status_sync pended.
	 */
	pending_phase = atomic_get(&phase);
	early_completion = k_sem_take(&completed, K_NO_WAIT);
	early_expiry = atomic_get(&expiry_in_isr);
	remaining = k_timer_remaining_get(&timer);

	/* A semaphore retains completion even if expiry precedes this take. */
	completion_result = k_sem_take(&completed, K_SECONDS(2));
	if (completion_result != 0) {
		/* Release a stuck timer waiter before cleaning up. */
		k_timer_stop(&timer);
	}
	join_result = k_thread_join(&worker_thread, K_SECONDS(1));
	if (join_result != 0) {
		k_thread_abort(&worker_thread);
	}
	k_timer_stop(&timer);
	k_thread_priority_set(self, original_priority);

	zassert_equal(pending_phase, 1, "Worker did not pend");
	zassert_equal(early_completion, -EBUSY, "Worker completed early");
	zassert_equal(early_expiry, 0, "Timer expired before pending check");
	zassert_true(remaining > 0, "Timer was no longer pending expiry");
	zassert_equal(completion_result, 0, "Completion signal was lost");
	zassert_equal(join_result, 0, "Worker failed to terminate");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback did not run in interrupt context");
	zassert_equal(atomic_get(&phase), 2, "Timer wait did not return");
	zassert_equal(received_status, 1, "Expected one timer expiration");
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
