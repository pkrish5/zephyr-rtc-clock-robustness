#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(2)
#define WAKE_DELAY K_MSEC(100)
#define MAX_WAKE_LATENCY K_SECONDS(1)
#define SLEEP_MARGIN K_MSEC(50)

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem resumed;
static int64_t sleep_started;
static int64_t sleep_elapsed;
static k_tid_t sleeper_tid;
static volatile bool sleeper_asleep;
static volatile bool wakeup_in_isr;

static void sleeper_entry(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	sleep_started = k_uptime_get();
	sleeper_asleep = true;
	(void)k_sleep(SLEEP_DURATION);
	sleep_elapsed = k_uptime_get() - sleep_started;
	k_sem_give(&resumed);
}

static void wakeup_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_in_isr = k_is_in_isr();
	if (sleeper_asleep) {
		k_wakeup(sleeper_tid);
	}
}

ZTEST(wakeup_from_isr, test_sleeping_thread_wakes_early)
{
	k_sem_init(&resumed, 0, 1);
	sleeper_asleep = false;
	wakeup_in_isr = false;
	sleep_elapsed = 0;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper_entry, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Wait until the thread has entered its sleep before scheduling the ISR. */
	while (!sleeper_asleep) {
		k_yield();
	}
	k_sleep(WAKE_DELAY);
	irq_offload(wakeup_isr, NULL);

	zassert_true(wakeup_in_isr, "wakeup callback did not run in ISR context");
	zassert_equal(k_sem_take(&resumed, MAX_WAKE_LATENCY), 0,
		      "sleeping thread did not report completion after wakeup");
	zassert_true(sleep_elapsed < (int64_t)SLEEP_DURATION - SLEEP_MARGIN,
		     "thread sleep duration was not shorter than requested by margin");
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
