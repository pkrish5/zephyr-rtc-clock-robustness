#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define TARGET_SLEEP_MS 500
#define WAKE_DELAY_MS  50
#define WAKE_MARGIN_MS 25

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem resumed_sem;
static k_tid_t sleeper_tid;
static int64_t sleep_started_ms;
static int64_t resumed_at_ms;
static bool wakeup_was_in_isr;

static void sleeper(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	sleep_started_ms = k_uptime_get();
	(void)k_sleep(K_MSEC(TARGET_SLEEP_MS));
	resumed_at_ms = k_uptime_get();
	k_sem_give(&resumed_sem);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_was_in_isr = k_is_in_isr();
	k_wakeup(sleeper_tid);
}

ZTEST(irq_wakeup, test_wakeup_sleeping_thread_from_isr)
{
	int64_t elapsed_ms;

	k_sem_init(&resumed_sem, 0, 1);
	wakeup_was_in_isr = false;
	resumed_at_ms = 0;
	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "failed to create sleeper thread");

	/* Allow the new thread to enter k_sleep() before arranging the IRQ. */
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	irq_offload(wake_from_isr, NULL);

	zassert_equal(k_sem_take(&resumed_sem, K_SECONDS(2)), 0,
		      "sleeper did not report completion");
	zassert_true(wakeup_was_in_isr, "k_wakeup was not called in ISR context");

	elapsed_ms = resumed_at_ms - sleep_started_ms;
	zassert_true(elapsed_ms < TARGET_SLEEP_MS - WAKE_MARGIN_MS,
		     "sleep was not shortened enough: elapsed %lld ms",
		     (long long)elapsed_ms);

	k_thread_join(sleeper_tid, K_SECONDS(1));
}

ZTEST_SUITE(irq_wakeup, NULL, NULL, NULL, NULL, NULL);
