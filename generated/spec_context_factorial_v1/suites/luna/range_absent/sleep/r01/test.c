#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(2)
#define WAKE_DELAY_MS 100
#define MAX_WAKE_ELAPSED_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem started_sem;
static struct k_sem completed_sem;
static k_tid_t sleeper_tid;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_wakeup(sleeper_tid);
}

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&started_sem);
	sleep_start_ms = k_uptime_get();
	k_sleep(SLEEP_DURATION);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed_sem);
}

ZTEST(k_sleep_wakeup, test_irq_wakes_sleeping_thread)
{
	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&completed_sem, 0, 1);
	sleep_start_ms = 0;
	sleep_end_ms = 0;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper_entry, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(5), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "failed to create sleeper thread");

	zassert_equal(k_sem_take(&started_sem, K_SECONDS(1)), 0,
		      "sleeper did not start");
	/* Let the sleeper enter k_sleep() before requesting the interrupt wakeup. */
	k_msleep(WAKE_DELAY_MS);
	irq_offload(wake_from_isr, NULL);

	zassert_equal(k_sem_take(&completed_sem, K_SECONDS(1)), 0,
		      "sleeper did not report completion after ISR wakeup");

	int64_t elapsed_ms = sleep_end_ms - sleep_start_ms;
	zassert_true(elapsed_ms >= WAKE_DELAY_MS,
		     "measured sleep duration (%lld ms) precedes wake delay",
		     (long long)elapsed_ms);
	zassert_true(elapsed_ms < MAX_WAKE_ELAPSED_MS,
		     "sleep duration (%lld ms) was not shorter than requested duration",
		     (long long)elapsed_ms);
}

ZTEST_SUITE(k_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
