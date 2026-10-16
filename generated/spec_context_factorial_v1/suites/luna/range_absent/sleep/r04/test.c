#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(5)
#define WAKE_DELAY_MS 100
#define MIN_EARLY_MARGIN_MS 100

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem sleeper_started;
static struct k_sem sleeper_done;
static k_tid_t sleeper_tid;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static bool wakeup_was_in_isr;

static void wakeup_isr(const void *unused)
{
	ARG_UNUSED(unused);

	wakeup_was_in_isr = k_is_in_isr();
	k_wakeup(sleeper_tid);
}

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&sleeper_started);
	sleep_start_ms = k_uptime_get();
	k_sleep(SLEEP_DURATION);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&sleeper_done);
}

ZTEST(k_wakeup_isr, test_wakeup_sleeping_thread)
{
	k_sem_init(&sleeper_started, 0, 1);
	k_sem_init(&sleeper_done, 0, 1);
	wakeup_was_in_isr = false;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper_entry, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "Failed to create sleeper thread");

	zassert_equal(k_sem_take(&sleeper_started, K_SECONDS(1)), 0,
		      "Sleeper did not start");
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	irq_offload(wakeup_isr, NULL);

	zassert_equal(k_sem_take(&sleeper_done, K_SECONDS(2)), 0,
		      "Sleeper did not report completion after ISR wakeup");
	zassert_true(wakeup_was_in_isr, "Wakeup callback was not in ISR context");
	zassert_true(sleep_end_ms >= sleep_start_ms,
		     "Invalid sleep duration timestamps");
	zassert_true(sleep_end_ms - sleep_start_ms <
		     (int64_t)K_MSEC(SLEEP_DURATION) - MIN_EARLY_MARGIN_MS,
		     "Thread did not resume sufficiently before requested timeout");

	k_thread_join(sleeper_tid, K_SECONDS(1));
}

ZTEST_SUITE(k_wakeup_isr, NULL, NULL, NULL, NULL, NULL);
