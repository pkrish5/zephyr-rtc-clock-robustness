#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(2)
#define WAKE_DELAY_MS 100
#define MIN_EARLY_MARGIN_MS 500
#define SEM_TIMEOUT K_SECONDS(5)

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem resumed_sem;
static volatile int64_t sleep_elapsed_ms;
static volatile bool wake_from_isr;

static void wake_target(const void *unused)
{
	ARG_UNUSED(unused);
	wake_from_isr = k_is_in_isr();
	k_wakeup(&sleeper_thread);
}

static void sleeper(void *a, void *b, void *c)
{
	int64_t start;

	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	start = k_uptime_get();
	(void)k_sleep(SLEEP_DURATION);
	sleep_elapsed_ms = k_uptime_get() - start;
	k_sem_give(&resumed_sem);
}

ZTEST(wakeup_from_isr, test_wakeup_sleeping_thread)
{
	k_sem_init(&resumed_sem, 0, 1);
	sleep_elapsed_ms = 0;
	wake_from_isr = false;

	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Let the target enter k_sleep() before issuing the offloaded ISR. */
	k_msleep(WAKE_DELAY_MS);
	irq_offload(wake_target, NULL);

	zassert_ok(k_sem_take(&resumed_sem, SEM_TIMEOUT), "sleeper did not resume");
	zassert_true(wake_from_isr, "wakeup callback did not run in ISR context");
	zassert_true(sleep_elapsed_ms < (int64_t)k_ticks_to_ms_ceil32(SLEEP_DURATION) -
		     MIN_EARLY_MARGIN_MS,
		     "sleep duration %lld ms was not sufficiently shorter than requested",
		     (long long)sleep_elapsed_ms);

	k_thread_join(&sleeper_thread, SEM_TIMEOUT);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
