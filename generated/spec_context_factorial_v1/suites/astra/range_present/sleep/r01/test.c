#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REQUESTED_MS 1000
#define WAKE_WINDOW_MS 250
#define MAX_OBSERVED_MS 750

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready;
static struct k_sem done;
static atomic_t wake_issued;
static atomic_t resumed;
static int64_t sleep_start;
static int64_t sleep_end;
static int64_t wake_elapsed;
static bool interrupt_context;
static bool asleep_at_wakeup;
static bool completion_after_wakeup;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* On one CPU, the controller cannot consume ready until we block.
	 * Scheduler locking prevents ready's give from preempting us.
	 * The lock is temporarily released by k_sleep().
	 */
	k_sched_lock();
	k_sem_give(&ready);
	sleep_start = k_uptime_get();
	k_sleep(K_MSEC(REQUESTED_MS));
	sleep_end = k_uptime_get();
	completion_after_wakeup = atomic_get(&wake_issued) != 0;
	atomic_set(&resumed, 1);
	k_sched_unlock();
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	k_tid_t target = (k_tid_t)arg;

	interrupt_context = k_is_in_isr();
	wake_elapsed = k_uptime_get() - sleep_start;
	/* The ready handoff establishes entry into sleep. This time check
	 * excludes natural timeout, including a timeout pending scheduling.
	 * No other code wakes or aborts the target before this callback.
	 */
	asleep_at_wakeup = atomic_get(&resumed) == 0 &&
		wake_elapsed >= 0 && wake_elapsed < WAKE_WINDOW_MS;
	atomic_set(&wake_issued, 1);
	k_wakeup(target);
}

ZTEST(isr_wakeup, test_wakeup_sleeping_thread)
{
	int ready_rc;
	int done_rc = -1;

	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	atomic_clear(&wake_issued);
	atomic_clear(&resumed);
	interrupt_context = false;
	asleep_at_wakeup = false;
	completion_after_wakeup = false;
	sleep_start = 0;
	sleep_end = 0;
	wake_elapsed = -1;

	/* Ordinary ZTEST runs in supervisor mode, even with TEST_USERSPACE. */
	k_tid_t target = k_thread_create(&sleeper_thread, sleeper_stack,
		K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
		NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	ready_rc = k_sem_take(&ready, K_MSEC(1000));
	if (ready_rc == 0) {
		irq_offload(wake_from_isr, target);
		done_rc = k_sem_take(&done, K_MSEC(500));
	}

	/* Clean up even if a check fails or the worker is still sleeping. */
	k_thread_abort(target);

	zassert_equal(ready_rc, 0, "Sleeper did not reach its sleep handoff");
	zassert_true(interrupt_context, "Wakeup callback was not in an ISR");
	zassert_true(asleep_at_wakeup,
		"Target was not demonstrably asleep when wakeup was issued");
	zassert_equal(done_rc, 0, "No completion event after ISR wakeup");
	zassert_true(completion_after_wakeup,
		"Sleeper resumed before the ISR issued wakeup");

	/* Require a 250 ms margin against the 1000 ms request, rather than
	 * a borderline comparison sensitive to uptime's ms resolution.
	 * Both measurements use kernel time, so HSI's +/-1% frequency
	 * tolerance does not require converting to external wall time.
	 * The 500 ms completion wait is a tested scheduling budget, not an
	 * ISR-delivery bound inferred from the oscillator specification.
	 */
	zassert_true(sleep_end >= sleep_start, "Invalid sleep timestamps");
	zassert_true(sleep_end - sleep_start < MAX_OBSERVED_MS,
		"ISR wakeup did not shorten sleep by the required margin");
}

ZTEST_SUITE(isr_wakeup, NULL, NULL, NULL, NULL, NULL);
