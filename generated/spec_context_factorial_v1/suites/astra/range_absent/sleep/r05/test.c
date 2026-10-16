#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REQUESTED_MS 2000
#define EARLY_LIMIT_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;

static struct {
	struct k_sem ready;
	struct k_sem done;
	k_tid_t tid;
	int64_t start_ms;
	int64_t elapsed_ms;
	int64_t wake_elapsed_ms;
	bool returned;
	bool in_isr;
	bool wake_before_return;
	bool wakeup_issued;
	bool completed_after_wakeup;
} state;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/*
	 * On this single CPU, the test cannot run after ready is given
	 * until k_sleep() blocks: the scheduler lock prevents preemption.
	 * A blocking call permits another thread to run while locked.
	 */
	k_sched_lock();
	k_sem_give(&state.ready);
	state.start_ms = k_uptime_get();
	k_sleep(K_MSEC(REQUESTED_MS));
	state.elapsed_ms = k_uptime_get() - state.start_ms;
	state.returned = true;
	state.completed_after_wakeup = state.wakeup_issued;
	k_sched_unlock();

	/* This event is the observable evidence that k_sleep returned. */
	k_sem_give(&state.done);
}

static void wake_isr(const void *arg)
{
	ARG_UNUSED(arg);
	state.in_isr = k_is_in_isr();
	state.wake_before_return = !state.returned;
	state.wake_elapsed_ms = k_uptime_get() - state.start_ms;
	k_wakeup(state.tid);
	/* The sleeping thread cannot execute until this ISR exits. */
	state.wakeup_issued = true;
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	int rc;

	state.returned = false;
	state.in_isr = false;
	state.wake_before_return = false;
	state.wakeup_issued = false;
	state.completed_after_wakeup = false;
	k_sem_init(&state.ready, 0, 1);
	k_sem_init(&state.done, 0, 1);

	state.tid = k_thread_create(&sleeper_thread, sleeper_stack,
		K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
		NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	rc = k_sem_take(&state.ready, K_SECONDS(1));
	if (rc != 0) {
		k_thread_abort(state.tid);
	}
	zassert_equal(rc, 0, "Sleeper did not reach the sleep handshake");

	irq_offload(wake_isr, NULL);
	rc = k_sem_take(&state.done, K_MSEC(EARLY_LIMIT_MS));
	/* Also clean up the thread if a broken wakeup leaves it asleep. */
	k_thread_abort(state.tid);

	zassert_true(state.in_isr, "Wakeup was not issued in interrupt context");
	zassert_true(state.wake_before_return,
		     "Target had already returned from k_sleep");
	zassert_true(state.wake_elapsed_ms >= 0 &&
		     state.wake_elapsed_ms < EARLY_LIMIT_MS,
		     "ISR did not run safely before the sleep deadline");
	zassert_equal(rc, 0, "No completion event after ISR wakeup");
	zassert_true(state.completed_after_wakeup,
		     "Thread completed before the ISR called k_wakeup");

	/*
	 * Require at least 1000 ms of early return. This deliberately wide
	 * margin tolerates tick rounding and normal scheduling latency,
	 * while excluding completion through the original 2000 ms timeout.
	 */
	zassert_true(state.elapsed_ms >= 0 &&
		     state.elapsed_ms < EARLY_LIMIT_MS,
		     "Sleep was not shortened by the required margin");
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
