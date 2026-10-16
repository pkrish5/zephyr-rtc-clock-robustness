#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <stdbool.h>

#define SLEEP_MS 2000
#define EARLY_LIMIT_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
K_SEM_DEFINE(ready, 0, 1);
K_SEM_DEFINE(done, 0, 1);

static volatile bool interrupt_context;
static volatile bool timeout_pending;
static volatile bool wakeup_returned;
static bool completion_after_wakeup;
static int64_t elapsed_ms;

static void sleeper(void *p1, void *p2, void *p3)
{
	(void)p1;
	(void)p2;
	(void)p3;

	/*
	 * On this single CPU, this cooperative thread cannot yield to the
	 * test between giving ready and blocking in k_sleep(). Thus taking
	 * ready lets the test proceed only after the sleeper has blocked.
	 */
	k_sem_give(&ready);
	int64_t start = k_uptime_get();

	k_sleep(K_MSEC(SLEEP_MS));
	elapsed_ms = k_uptime_get() - start;
	completion_after_wakeup = wakeup_returned;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	(void)arg;
	interrupt_context = k_is_in_isr();
	/* The target's only blocking operation so far is k_sleep(). */
	timeout_pending =
		k_thread_timeout_remaining_ticks(&sleeper_thread) > 0;
	k_wakeup(&sleeper_thread);
	/* The target cannot run until this ISR exits on the single CPU. */
	wakeup_returned = true;
}

ZTEST(sleep_wakeup, test_interrupt_wakes_sleeper)
{
	k_sem_reset(&ready);
	k_sem_reset(&done);
	interrupt_context = false;
	timeout_pending = false;
	wakeup_returned = false;
	completion_after_wakeup = false;
	elapsed_ms = -1;

	k_tid_t tid = k_thread_create(&sleeper_thread, sleeper_stack,
		K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
		NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	int rc = k_sem_take(&ready, K_MSEC(1000));

	if (rc != 0) {
		k_thread_abort(tid);
		zassert_equal(rc, 0, "Sleeper did not reach its sleep sequence");
		return;
	}

	irq_offload(wake_from_isr, NULL);
	rc = k_sem_take(&done, K_MSEC(EARLY_LIMIT_MS));
	/* Clean up even when a check fails. All worker data is static. */
	k_thread_abort(tid);

	zassert_true(interrupt_context, "Wakeup was not issued in an ISR");
	zassert_true(timeout_pending, "Target had no pending sleep timeout");
	zassert_equal(rc, 0, "No completion event after ISR wakeup");
	zassert_true(completion_after_wakeup,
		     "Target completed before the ISR wakeup returned");

	/*
	 * Require at least 1000 ms of early completion. This deliberately
	 * large margin dwarfs tick rounding and the documented 1% HSI
	 * error (about 20 ms over two seconds). Both measurements use
	 * kernel time. The one-second response budget is an executable
	 * test criterion, not a latency guarantee inferred from HSI
	 * accuracy; excessive delivery or scheduling delay fails the test.
	 */
	zassert_true(elapsed_ms >= 0 && elapsed_ms < EARLY_LIMIT_MS,
		     "Sleep lasted %lld ms; expected less than %d ms",
		     (long long)elapsed_ms, EARLY_LIMIT_MS);
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
