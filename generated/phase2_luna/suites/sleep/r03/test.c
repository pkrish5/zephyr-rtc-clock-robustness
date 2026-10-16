#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_DURATION K_SECONDS(5)
#define WAKE_DELAY_MS 100
#define MAX_SLEEP_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem resumed_sem;
static k_tid_t sleeper_id;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static bool wakeup_from_isr;

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	sleep_start_ms = k_uptime_get();
	(void)k_sleep(SLEEP_DURATION);
	sleep_end_ms = k_uptime_get();
	k_sem_give(&resumed_sem);
}

static void wakeup_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_from_isr = k_is_in_isr();
	k_wakeup(sleeper_id);
}

ZTEST(k_wakeup_sleep, test_isr_wakes_sleeping_thread)
{
	k_sem_init(&resumed_sem, 0, 1);
	wakeup_from_isr = false;
	sleep_start_ms = 0;
	sleep_end_ms = 0;

	sleeper_id = k_thread_create(&sleeper_thread, sleeper_stack,
				     K_THREAD_STACK_SIZEOF(sleeper_stack),
				     sleeper_entry, NULL, NULL, NULL,
				     K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	/* Poll until the sleeper has entered k_sleep(), with a bounded timeout. */
	for (int i = 0; i < 1000 && !k_thread_is_sleeping(sleeper_id); ++i) {
		k_sleep(K_MSEC(1));
	}
	zassert_true(k_thread_is_sleeping(sleeper_id), "target did not enter sleep");

	k_sleep(K_MSEC(WAKE_DELAY_MS));
	zassert_true(k_thread_is_sleeping(sleeper_id), "target was not asleep before IRQ");
	irq_offload(wakeup_isr, NULL);

	zassert_equal(k_sem_take(&resumed_sem, K_SECONDS(2)), 0,
		      "sleeping thread did not signal completion after wakeup");
	zassert_true(wakeup_from_isr, "k_wakeup was not called in interrupt context");
	zassert_true(sleep_end_ms >= sleep_start_ms, "invalid sleep timestamps");
	zassert_true((sleep_end_ms - sleep_start_ms) < MAX_SLEEP_MS,
		     "observed sleep duration was not shorter than requested");

	k_thread_join(sleeper_id, K_SECONDS(1));
}

ZTEST_SUITE(k_wakeup_sleep, NULL, NULL, NULL, NULL, NULL);
