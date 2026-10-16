#include <zephyr/kernel.h>
#include <zephyr/irq.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define SLEEP_MS 2000
#define EARLY_LIMIT_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready;
static struct k_sem done;

static struct {
	bool in_isr;
	bool asleep_at_wakeup;
	bool wakeup_returned;
	bool completion_after_wakeup;
	int64_t elapsed_ms;
} result;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/*
	 * This cooperative thread cannot be preempted by the test thread
	 * after giving ready. Its next scheduling point is k_sleep().
	 */
	int64_t start = k_uptime_get();

	k_sem_give(&ready);
	k_sleep(K_MSEC(SLEEP_MS));
	result.elapsed_ms = k_uptime_get() - start;
	result.completion_after_wakeup = result.wakeup_returned;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	struct k_thread *thread = (struct k_thread *)arg;
	unsigned int key = irq_lock();

	result.in_isr = k_is_in_isr();
	/*
	 * The ready handshake establishes that k_sleep() has been entered.
	 * A still-pending timeout establishes that it has not expired.
	 * Lock interrupts across the check and wakeup to exclude expiry
	 * between them on this single-CPU board.
	 */
	result.asleep_at_wakeup =
		k_thread_timeout_remaining_ticks(thread) > 0;
	k_wakeup(thread);
	result.wakeup_returned = true;

	irq_unlock(key);
}

ZTEST(sleep_isr_wakeup, test_interrupt_wakes_sleeping_thread)
{
	int rc;

	result = (typeof(result)){0};
	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);

	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	rc = k_sem_take(&ready, K_MSEC(1000));
	if (rc != 0) {
		k_thread_abort(&sleeper_thread);
	}
	zassert_equal(rc, 0, "Sleeper did not reach its sleep handshake");

	irq_offload(wake_from_isr, &sleeper_thread);

	/* Allow natural expiry to complete too; the timing check rejects it. */
	rc = k_sem_take(&done, K_MSEC(SLEEP_MS + 1000));
	if (rc != 0) {
		k_thread_abort(&sleeper_thread);
	}
	zassert_equal(rc, 0, "Sleeper did not signal completion");

	rc = k_thread_join(&sleeper_thread, K_MSEC(1000));
	if (rc != 0) {
		k_thread_abort(&sleeper_thread);
	}
	zassert_equal(rc, 0, "Sleeper did not exit");

	zassert_true(result.in_isr, "Wakeup was not issued in an ISR");
	zassert_true(result.asleep_at_wakeup,
		     "Target had no pending sleep timeout at wakeup");
	zassert_true(result.completion_after_wakeup,
		     "Completion preceded the ISR wakeup");

	/*
	 * Require a full one-second margin against the two-second request.
	 * Both durations use Zephyr's clock, so oscillator error largely
	 * cancels; the 1% HSI bound is not a delivery-latency guarantee.
	 * This is an explicit, generous test acceptance budget, not a
	 * hardware-derived latency bound. Immediate offload should finish
	 * far inside it on this otherwise idle board. The measured interval
	 * also includes the ready-handshake overhead, conservatively.
	 */
	zassert_true(result.elapsed_ms >= 0 &&
		     result.elapsed_ms < EARLY_LIMIT_MS,
		     "Sleep took %lld ms; expected less than %d ms (request %d ms)",
		     (long long)result.elapsed_ms, EARLY_LIMIT_MS, SLEEP_MS);
}

/* Use a supervisor test even when CONFIG_TEST_USERSPACE is enabled. */
ZTEST_SUITE(sleep_isr_wakeup, NULL, NULL, NULL, NULL, NULL);
