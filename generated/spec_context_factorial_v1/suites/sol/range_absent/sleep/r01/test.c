#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define SLEEP_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(sleep_started, 0, 1);
K_SEM_DEFINE(completed, 0, 1);

static struct k_thread worker_thread;
static volatile bool wakeup_was_in_isr;
static int32_t remaining_ms;
static int64_t elapsed_ms;

static void sleeper(void *arg1, void *arg2, void *arg3)
{
	int64_t start = k_uptime_get();

	k_sem_give(&sleep_started);
	remaining_ms = k_sleep(K_MSEC(SLEEP_MS));
	elapsed_ms = k_uptime_get() - start;
	k_sem_give(&completed);
}

static void wake_sleeper(const void *arg)
{
	wakeup_was_in_isr = k_is_in_isr();
	k_wakeup((k_tid_t)arg);
}

ZTEST(thread_wakeup, test_wakeup_from_isr)
{
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_PREEMPT(8), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&sleep_started, K_SECONDS(1)));
	/* Let the single CPU schedule the worker into k_sleep(). */
	k_sleep(K_MSEC(50));
	zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);

	irq_offload(wake_sleeper, &worker_thread);
	zassert_true(wakeup_was_in_isr);
	zassert_ok(k_sem_take(&completed, K_MSEC(500)));
	zassert_true(remaining_ms > 0);
	zassert_true(elapsed_ms < SLEEP_MS - 200);
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
