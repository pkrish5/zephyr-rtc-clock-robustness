#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define SLEEP_MS 2000
#define EARLY_MARGIN_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;

static struct {
	struct k_sem ready;
	struct k_sem done;
	k_tid_t tid;
	int64_t start_ms;
	int64_t wake_ms;
	int64_t end_ms;
	volatile bool resumed;
	volatile bool in_isr;
	volatile bool asleep_at_wakeup;
	volatile bool wakeup_issued;
	bool saw_wakeup;
} state;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	state.start_ms = k_uptime_get();
	/*
	 * This thread is cooperative. On this single CPU, giving ready
	 * cannot let the test thread run until we block in k_sleep().
	 */
	k_sem_give(&state.ready);
	k_sleep(K_MSEC(SLEEP_MS));
	state.end_ms = k_uptime_get();
	state.saw_wakeup = state.wakeup_issued;
	state.resumed = true;
	k_sem_give(&state.done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	state.in_isr = k_is_in_isr();
	state.wake_ms = k_uptime_get();
	/*
	 * The ready handshake establishes entry into sleep. Requiring a
	 * full second before its earliest expiry excludes timeout races.
	 */
	state.asleep_at_wakeup = !state.resumed &&
		(state.wake_ms - state.start_ms <
		 SLEEP_MS - EARLY_MARGIN_MS);
	k_wakeup(state.tid);
	/* The sleeper cannot execute until this ISR returns. */
	state.wakeup_issued = true;
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	int rc;

	k_sem_init(&state.ready, 0, 1);
	k_sem_init(&state.done, 0, 1);
	state.resumed = false;
	state.in_isr = false;
	state.asleep_at_wakeup = false;
	state.wakeup_issued = false;
	state.saw_wakeup = false;

	state.tid = k_thread_create(&sleeper_thread, sleeper_stack,
		K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
		NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	rc = k_sem_take(&state.ready, K_SECONDS(1));
	if (rc != 0) {
		k_thread_abort(state.tid);
	}
	zassert_equal(rc, 0, "Sleeper did not signal readiness");

	irq_offload(wake_from_isr, NULL);

	rc = k_sem_take(&state.done, K_MSEC(SLEEP_MS + 500));
	if (rc != 0) {
		k_thread_abort(state.tid);
	}
	zassert_equal(rc, 0, "Sleeper did not signal completion");

	rc = k_thread_join(state.tid, K_SECONDS(1));
	if (rc != 0) {
		k_thread_abort(state.tid);
	}
	zassert_equal(rc, 0, "Sleeper did not exit");
	zassert_true(state.in_isr, "Wakeup was not issued from an ISR");
	zassert_true(state.asleep_at_wakeup,
		     "Target was not safely within its sleep interval");
	zassert_true(state.saw_wakeup,
		     "Sleeper completed before the ISR issued wakeup");
	zassert_true(state.end_ms >= state.wake_ms,
		     "Completion preceded ISR wakeup");
	/*
	 * Require at least one second saved from a two-second sleep.
	 * This comfortably exceeds tick quantization and millisecond
	 * timestamp rounding, while allowing normal dispatch overhead.
	 */
	zassert_true(state.end_ms - state.start_ms <
		     SLEEP_MS - EARLY_MARGIN_MS,
		     "Sleep did not finish with the required early margin");
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
