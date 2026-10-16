#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP_MS 2000
#define EARLY_WAKE_LIMIT_MS 1500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
K_SEM_DEFINE(sleep_started, 0, 1);
K_SEM_DEFINE(sleep_finished, 0, 1);

static struct k_thread sleeper_thread;
static k_tid_t sleeper_tid;
static atomic_t wakeup_in_isr;
static int64_t elapsed_ms;

static void sleeper(void *arg1, void *arg2, void *arg3)
{
	int64_t start_ms = k_uptime_get();

	k_sem_give(&sleep_started);
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	elapsed_ms = k_uptime_get() - start_ms;
	k_sem_give(&sleep_finished);
}

static void wakeup_offload(const void *arg)
{
	atomic_set(&wakeup_in_isr, k_is_in_isr());
	k_wakeup(sleeper_tid);
}

ZTEST(wakeup_from_isr, test_wakeup_interrupts_sleep)
{
	sleeper_tid = k_thread_create(&sleeper_thread, sleeper_stack,
				      K_THREAD_STACK_SIZEOF(sleeper_stack),
				      sleeper, NULL, NULL, NULL,
				      K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&sleep_started, K_SECONDS(1)), 0,
		      "sleeper did not start");

	/* While this thread sleeps, the sleeper can enter k_sleep(). */
	k_sleep(K_MSEC(20));
	irq_offload(wakeup_offload, NULL);

	zassert_true(atomic_get(&wakeup_in_isr),
		     "wakeup was not issued from interrupt context");
	zassert_equal(k_sem_take(&sleep_finished, K_SECONDS(1)), 0,
		      "sleeper did not report completion after wakeup");
	/* The 500 ms margin is generous relative to the 20 ms setup delay. */
	zassert_true(elapsed_ms < EARLY_WAKE_LIMIT_MS,
		     "sleep lasted too long: %lld ms", (long long)elapsed_ms);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
