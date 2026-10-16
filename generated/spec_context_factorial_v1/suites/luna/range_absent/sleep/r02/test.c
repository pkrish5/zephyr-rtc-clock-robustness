#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define WAKE_DELAY_MS 50
#define REQUESTED_SLEEP_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem started_sem;
static struct k_sem completed_sem;
static volatile bool wakeup_from_isr;
static volatile bool wakeup_target_was_asleep;
static volatile int64_t sleep_elapsed_ms;
static volatile int64_t requested_sleep_ms;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	requested_sleep_ms = REQUESTED_SLEEP_MS;
	k_sem_give(&started_sem);
	int64_t start_ms = k_uptime_get();
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	sleep_elapsed_ms = k_uptime_get() - start_ms;
	k_sem_give(&completed_sem);
}

static void wakeup_isr(const void *data)
{
	ARG_UNUSED(data);

	wakeup_from_isr = k_is_in_isr();
	wakeup_target_was_asleep = (k_thread_state_get(&sleeper_thread) &
				    (K_STATE_SLEEPING | K_STATE_SUSPENDED)) != 0U;
	k_wakeup(&sleeper_thread);
}

ZTEST(wakeup_from_isr, test_sleeping_thread_wakes_early)
{
	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);
	wakeup_from_isr = false;
	wakeup_target_was_asleep = false;
	sleep_elapsed_ms = -1;
	requested_sleep_ms = 0;

	k_tid_t tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(tid, "Failed to create sleeper thread");
	zassert_equal(k_sem_take(&started_sem, K_SECONDS(1)), 0,
		      "Sleeper did not start");

	/* Let the sleeper enter k_sleep before triggering the offloaded ISR. */
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	irq_offload(wakeup_isr, NULL);

	zassert_equal(k_sem_take(&completed_sem, K_SECONDS(1)), 0,
		      "Sleeper did not report completion");
	zassert_true(wakeup_from_isr, "Wakeup callback was not in ISR context");
	zassert_true(wakeup_target_was_asleep,
		     "Target thread was not asleep when wakeup was issued");
	zassert_true(sleep_elapsed_ms < requested_sleep_ms - WAKE_DELAY_MS,
		     "Sleep duration (%lld ms) was not shorter than requested (%lld ms) with margin",
		     (long long)sleep_elapsed_ms, (long long)requested_sleep_ms);

	k_thread_abort(tid);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
