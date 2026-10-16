#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP_MS 5000
#define STARTUP_SETTLE_MS 50
#define COMPLETION_TIMEOUT K_SECONDS(2)

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready_sem;
static struct k_sem completion_sem;
static k_tid_t sleeper_tid;
static int64_t elapsed_ms;
static bool wakeup_was_from_isr;

static void wakeup_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	wakeup_was_from_isr = k_is_in_isr();
	k_wakeup(sleeper_tid);
}

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&ready_sem);
	int64_t started_ms = k_uptime_get();
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	elapsed_ms = k_uptime_get() - started_ms;
	k_sem_give(&completion_sem);
}

ZTEST(wakeup_from_isr, test_wakes_sleeping_thread_early)
{
	k_sem_init(&ready_sem, 0, 1);
	k_sem_init(&completion_sem, 0, 1);
	elapsed_ms = REQUESTED_SLEEP_MS;
	wakeup_was_from_isr = false;

	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper_entry, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(5), 0, K_NO_WAIT);
	zassert_not_null(sleeper_tid, "Failed to create sleeper thread");

	zassert_equal(k_sem_take(&ready_sem, K_SECONDS(1)), 0,
		      "Sleeper did not start");

	/* Let the sleeper enter k_sleep before delivering the interrupt. */
	k_sleep(K_MSEC(STARTUP_SETTLE_MS));
	irq_offload(wakeup_from_isr, NULL);

	zassert_equal(k_sem_take(&completion_sem, COMPLETION_TIMEOUT), 0,
		      "Sleeper did not report completion after wakeup");
	zassert_true(wakeup_was_from_isr, "Wakeup callback was not in ISR context");
	zassert_true(elapsed_ms < REQUESTED_SLEEP_MS - 1000,
		     "Sleep duration (%lld ms) was not shorter than requested with margin",
		     (long long)elapsed_ms);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
