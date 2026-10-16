#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define REQUESTED_SLEEP K_SECONDS(2)
#define EARLY_LIMIT_MS 1500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready;
static struct k_sem go;
static struct k_sem done;
static int64_t elapsed_ms;
static bool wakeup_in_isr;

static void sleeper(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sem_give(&ready);
	k_sem_take(&go, K_FOREVER);

	int64_t start_ms = k_uptime_get();
	k_sleep(REQUESTED_SLEEP);
	elapsed_ms = k_uptime_get() - start_ms;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	wakeup_in_isr = k_is_in_isr();
	k_wakeup(&sleeper_thread);
}

ZTEST(thread_wakeup, test_wakeup_from_isr)
{
	k_sem_init(&ready, 0, 1);
	k_sem_init(&go, 0, 1);
	k_sem_init(&done, 0, 1);
	wakeup_in_isr = false;
	elapsed_ms = -1;

	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready, K_SECONDS(1)), 0);
	k_sem_give(&go);
	/* Yield the single CPU so the worker can enter its two-second sleep. */
	k_sleep(K_MSEC(100));
	zassert_not_equal(k_sem_take(&done, K_NO_WAIT), 0);

	irq_offload(wake_from_isr, NULL);
	zassert_true(wakeup_in_isr);
	zassert_equal(k_sem_take(&done, K_SECONDS(1)), 0);
	zassert_true(elapsed_ms >= 0 && elapsed_ms < EARLY_LIMIT_MS,
		     "sleep lasted %lld ms", (long long)elapsed_ms);
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
