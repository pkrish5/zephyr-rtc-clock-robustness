#include <stdbool.h>
#include <stdint.h>

#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_SECONDS(1)
#define EARLY_LIMIT_MS 750

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
K_SEM_DEFINE(ready, 0, 1);
K_SEM_DEFINE(done, 0, 1);

static struct k_thread sleeper;
static volatile bool wakeup_in_isr;
static int64_t elapsed_ms;

static void sleeper_entry(void *a, void *b, void *c)
{
	int64_t start = k_uptime_get();

	/* This thread has higher priority than the test thread. On this
	 * single-CPU board, the test thread runs only after k_sleep blocks.
	 */
	k_sem_give(&ready);
	k_sleep(SLEEP_TIME);
	elapsed_ms = k_uptime_get() - start;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_in_isr = k_is_in_isr();
	k_wakeup(&sleeper);
}

ZTEST(wakeup_from_isr, test_sleep_wakeup)
{
	int priority = k_thread_priority_get(k_current_get()) - 1;

	wakeup_in_isr = false;
	k_thread_create(&sleeper, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper_entry,
			NULL, NULL, NULL, priority, 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&ready, K_SECONDS(2)));
	irq_offload(wake_from_isr, NULL);
	zassert_true(wakeup_in_isr, "wakeup was not issued from an ISR");
	zassert_ok(k_sem_take(&done, K_SECONDS(2)),
		   "sleeping thread did not report completion");
	zassert_true(elapsed_ms < EARLY_LIMIT_MS,
		     "sleep duration was not sufficiently shorter than requested");
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
