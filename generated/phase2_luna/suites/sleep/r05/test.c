#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(5)
#define WAKE_DELAY_MS  100
#define MAX_WAIT_MS    2000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem sleeper_started;
static struct k_sem sleeper_done;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static k_tid_t sleeper_tid;

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	/* The caller waits for sleeper_started before offloading this ISR. */
	k_wakeup(sleeper_tid);
}

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&sleeper_started);
	sleep_start_ms = k_uptime_get();
	(void)k_sleep(SLEEP_DURATION);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&sleeper_done);
}

ZTEST(wakeup_from_isr, test_wakeup_shortens_sleep)
{
	k_sem_init(&sleeper_started, 0, 1);
	k_sem_init(&sleeper_done, 0, 1);
	sleep_start_ms = 0;
	sleep_end_ms = 0;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper_entry, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "failed to create sleeper thread");

	zassert_equal(k_sem_take(&sleeper_started, K_MSEC(MAX_WAIT_MS)), 0,
		      "sleeper did not start");

	/* Allow the thread to enter k_sleep() before generating the interrupt. */
	k_msleep(WAKE_DELAY_MS);
	irq_offload(wake_from_isr, NULL);

	zassert_equal(k_sem_take(&sleeper_done, K_MSEC(MAX_WAIT_MS)), 0,
		      "sleeper did not report completion after ISR wakeup");

	int64_t elapsed_ms = sleep_end_ms - sleep_start_ms;
	/* Five seconds requested, with a 2-second bound to allow scheduling jitter. */
	zassert_true(elapsed_ms >= 0, "invalid measured sleep duration: %lld ms",
		     (long long)elapsed_ms);
	zassert_true(elapsed_ms < 3000,
		     "sleep was not shortened: elapsed %lld ms", (long long)elapsed_ms);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
