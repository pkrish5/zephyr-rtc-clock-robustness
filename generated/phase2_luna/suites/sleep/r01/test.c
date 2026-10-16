#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(5)
#define WAKE_DELAY_MS 100
#define MIN_EARLY_MARGIN_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready_sem;
static struct k_sem done_sem;
static k_tid_t sleeper_tid;
static int64_t sleep_started_ms;
static int64_t sleep_finished_ms;
static volatile bool wake_issued_in_isr;

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	wake_issued_in_isr = k_is_in_isr();
	k_wakeup(sleeper_tid);
}

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&ready_sem);
	sleep_started_ms = k_uptime_get();
	(void)k_sleep(SLEEP_DURATION);
	sleep_finished_ms = k_uptime_get();
	k_sem_give(&done_sem);
}

ZTEST(wakeup, test_wakeup_sleeping_thread_from_isr)
{
	k_sem_init(&ready_sem, 0, 1);
	k_sem_init(&done_sem, 0, 1);
	wake_issued_in_isr = false;
	sleep_started_ms = 0;
	sleep_finished_ms = 0;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "Could not create sleeper thread");

	zassert_equal(k_sem_take(&ready_sem, K_SECONDS(1)), 0,
		      "Sleeper did not start sleeping");
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	irq_offload(wake_from_isr, NULL);

	zassert_equal(k_sem_take(&done_sem, K_SECONDS(2)), 0,
		      "Sleeper did not report completion after ISR wakeup");
	zassert_true(wake_issued_in_isr, "Wakeup callback did not run in ISR context");
	zassert_true(sleep_finished_ms >= sleep_started_ms,
		     "Invalid measured sleep interval");
	zassert_true((sleep_finished_ms - sleep_started_ms) <
		     (k_ticks_to_ms_floor64(SLEEP_DURATION.ticks) - MIN_EARLY_MARGIN_MS),
		     "Sleeper did not resume sufficiently before requested duration");
}

ZTEST_SUITE(wakeup, NULL, NULL, NULL, NULL, NULL);
