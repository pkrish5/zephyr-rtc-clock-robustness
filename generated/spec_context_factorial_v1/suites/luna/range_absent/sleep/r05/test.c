#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP K_SECONDS(2)
#define WAKE_DELAY_MS 100
#define WAKE_MARGIN_MS 500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem started;
static struct k_sem completed;
static k_tid_t sleeper_tid;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static int64_t wake_request_ms;

static void sleeper(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&started);
	sleep_start_ms = k_uptime_get();
	k_sleep(REQUESTED_SLEEP);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&completed);
}

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	zassert_true(k_is_in_isr(), "wakeup callback must run in interrupt context");
	wake_request_ms = k_uptime_get();
	k_wakeup(sleeper_tid);
}

ZTEST(wakeup_from_isr, test_sleeping_thread_wakes_early)
{
	k_sem_init(&started, 0, 1);
	k_sem_init(&completed, 0, 1);
	sleep_start_ms = 0;
	sleep_end_ms = 0;
	wake_request_ms = 0;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "failed to create sleeper thread");
	zassert_ok(k_sem_take(&started, K_SECONDS(1)), "sleeper did not start");

	/* The delay gives the worker time to enter k_sleep before offloading the ISR. */
	k_msleep(WAKE_DELAY_MS);
	irq_offload(wake_from_isr, NULL);

	zassert_ok(k_sem_take(&completed, K_SECONDS(1)), "thread did not report completion");
	zassert_true(wake_request_ms >= sleep_start_ms,
		     "ISR wakeup timestamp preceded requested sleep");
	zassert_true((sleep_end_ms - sleep_start_ms) <
		     (k_ticks_to_ms_floor64(REQUESTED_SLEEP.ticks) - WAKE_MARGIN_MS),
		     "thread did not resume substantially before sleep timeout");
	zassert_true(sleep_end_ms >= wake_request_ms,
		     "completion timestamp preceded ISR wakeup");
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
