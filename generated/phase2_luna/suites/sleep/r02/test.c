#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP K_SECONDS(5)
#define WAKE_DELAY K_MSEC(100)
#define SEM_TIMEOUT K_SECONDS(2)
#define MIN_EARLY_MARGIN_MS 100

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem sleeping_sem;
static struct k_sem completed_sem;
static k_tid_t sleeper_tid;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static bool wakeup_from_isr;

static void sleeper(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&sleeping_sem);
	sleep_start_ms = k_uptime_get();
	k_sleep(REQUESTED_SLEEP);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed_sem);
}

static void wake_target_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_from_isr = k_is_in_isr();
	k_wakeup(sleeper_tid);
}

ZTEST(thread_wakeup, test_isr_wakes_sleeping_thread_early)
{
	k_sem_init(&sleeping_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);
	wakeup_from_isr = false;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "failed to create sleeper thread");

	zassert_equal(k_sem_take(&sleeping_sem, SEM_TIMEOUT), 0,
		      "sleeper did not start");

	/* Let the sleeper enter k_sleep() before delivering the offloaded IRQ. */
	k_sleep(WAKE_DELAY);
	irq_offload(wake_target_isr, NULL);

	zassert_equal(k_sem_take(&completed_sem, SEM_TIMEOUT), 0,
		      "sleeper did not signal completion after wakeup");
	zassert_true(wakeup_from_isr, "wakeup callback did not run in ISR context");
	zassert_true(sleep_end_ms - sleep_start_ms <
		     (int64_t)k_ticks_to_ms_ceil32(REQUESTED_SLEEP.ticks) -
		     MIN_EARLY_MARGIN_MS,
		     "observed sleep was not shorter than requested with margin");

	k_thread_join(sleeper_tid, K_SECONDS(1));
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
