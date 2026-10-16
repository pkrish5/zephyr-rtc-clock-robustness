#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 2000
#define EARLY_MARGIN_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready;
static struct k_sem done;
static atomic_t phase;
static atomic_t wake_issued;

static bool callback_in_isr;
static atomic_val_t callback_phase;
static bool resumed_after_wakeup;
static int32_t sleep_remaining_ms;
static int64_t elapsed_ms;

enum {
	INITIAL,
	ENTERING_SLEEP,
	FINISHED
};

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	atomic_set(&phase, ENTERING_SLEEP);
	k_sem_give(&ready);

	int64_t start_ms = k_uptime_get();

	sleep_remaining_ms = k_sleep(K_MSEC(SLEEP_MS));
	elapsed_ms = k_uptime_get() - start_ms;
	resumed_after_wakeup = atomic_get(&wake_issued) != 0;
	atomic_set(&phase, FINISHED);
	k_sem_give(&done);
}

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	callback_in_isr = k_is_in_isr();
	callback_phase = atomic_get(&phase);
	atomic_set(&wake_issued, 1);
	k_wakeup(&sleeper_thread);
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	atomic_set(&phase, INITIAL);
	atomic_set(&wake_issued, 0);
	callback_in_isr = false;
	callback_phase = INITIAL;
	resumed_after_wakeup = false;
	sleep_remaining_ms = 0;
	elapsed_ms = 0;

	/*
	 * On this single CPU, the cooperative worker cannot be preempted by
	 * the test thread after giving ready. It runs until k_sleep blocks.
	 * Thus, after taking ready, the test can offload the wakeup while the
	 * worker sleeps. The ISR phase check also detects prior expiration.
	 */
	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	int rc = k_sem_take(&ready, K_SECONDS(1));

	if (rc != 0) {
		k_thread_abort(&sleeper_thread);
	}
	zassert_equal(rc, 0, "Worker did not reach sleep");

	irq_offload(wake_from_isr, NULL);

	rc = k_sem_take(&done, K_SECONDS(3));
	/* Ensure the worker is stopped even if completion timed out. */
	k_thread_abort(&sleeper_thread);

	zassert_true(callback_in_isr, "Wakeup was not issued from an ISR");
	zassert_equal(callback_phase, ENTERING_SLEEP,
		      "Worker had already finished before ISR wakeup");
	zassert_equal(rc, 0, "Worker did not signal completion");
	zassert_true(resumed_after_wakeup, "Worker resumed before ISR wakeup");
	zassert_true(sleep_remaining_ms > 0, "Sleep expired normally");

	/*
	 * Allow up to one second for interrupt and scheduling latency, but
	 * require waking at least one second early. This margin is far larger
	 * than tick rounding or millisecond uptime measurement uncertainty.
	 */
	zassert_true(elapsed_ms >= 0 &&
		     elapsed_ms < SLEEP_MS - EARLY_MARGIN_MS,
		     "Worker did not resume sufficiently early");
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
