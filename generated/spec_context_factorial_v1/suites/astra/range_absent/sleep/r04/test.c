#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define SLEEP_MS 2000
#define COMPLETION_TIMEOUT_MS 1000
#define EARLY_MARGIN_MS 500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
K_SEM_DEFINE(ready, 0, 1);
K_SEM_DEFINE(done, 0, 1);

static struct {
	k_tid_t tid;
	int64_t start_ms;
	int64_t elapsed_ms;
	int64_t wake_elapsed_ms;
	atomic_t resumed;
	atomic_t wake_issued;
	bool interrupt_context;
	bool resumed_before_wakeup;
	bool saw_wakeup;
} state;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/*
	 * On this single CPU, the equal-priority test thread cannot run
	 * after ready is given until this thread blocks in k_sleep().
	 */
	k_sched_lock();
	k_sem_give(&ready);
	state.start_ms = k_uptime_get();
	k_sleep(K_MSEC(SLEEP_MS));
	state.elapsed_ms = k_uptime_get() - state.start_ms;
	state.saw_wakeup = atomic_get(&state.wake_issued) != 0;
	atomic_set(&state.resumed, 1);
	k_sched_unlock();

	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	state.interrupt_context = k_is_in_isr();
	state.resumed_before_wakeup = atomic_get(&state.resumed) != 0;
	state.wake_elapsed_ms = k_uptime_get() - state.start_ms;
	k_wakeup(state.tid);
	/* The awakened thread cannot execute until this ISR exits. */
	atomic_set(&state.wake_issued, 1);
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	int rc;

	k_sem_reset(&ready);
	k_sem_reset(&done);
	atomic_clear(&state.resumed);
	atomic_clear(&state.wake_issued);
	state.interrupt_context = false;
	state.resumed_before_wakeup = false;
	state.saw_wakeup = false;

	state.tid = k_thread_create(&sleeper_thread, sleeper_stack,
		K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
		NULL, NULL, NULL, k_thread_priority_get(k_current_get()),
		0, K_NO_WAIT);

	rc = k_sem_take(&ready, K_SECONDS(1));
	if (rc != 0) {
		k_thread_abort(state.tid);
		zassert_equal(rc, 0, "Sleeper did not reach sleep handoff");
		return;
	}

	irq_offload(wake_from_isr, NULL);
	rc = k_sem_take(&done, K_MSEC(COMPLETION_TIMEOUT_MS));

	/* Clean up even if completion timed out, before any assertion. */
	k_thread_abort(state.tid);

	zassert_true(state.interrupt_context, "Wakeup was not issued in ISR");
	zassert_false(state.resumed_before_wakeup,
		"Target had already resumed before ISR wakeup");
	zassert_true(state.wake_elapsed_ms >= 0 &&
		state.wake_elapsed_ms < SLEEP_MS - EARLY_MARGIN_MS,
		"ISR did not run safely before the sleep deadline");
	zassert_equal(rc, 0, "No completion event after ISR wakeup");
	zassert_true(state.saw_wakeup,
		"Sleeper resumed before ISR wakeup was recorded");

	/*
	 * No delay is intentionally inserted before wakeup. A 500 ms
	 * margin is far larger than STM32F4 timer-tick rounding; allowing
	 * up to 1500 ms still tolerates substantial scheduling overhead.
	 */
	zassert_true(state.elapsed_ms >= 0 &&
		state.elapsed_ms < SLEEP_MS - EARLY_MARGIN_MS,
		"Sleep did not finish at least 500 ms early (elapsed %lld ms)",
		(long long)state.elapsed_ms);
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
