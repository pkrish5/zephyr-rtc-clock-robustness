#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define SLEEP_MS 1000
#define WAKE_DELAY_MS 20

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(ready, 0, 1);
K_SEM_DEFINE(done, 0, 1);

static struct k_thread worker_thread;
static volatile bool sleep_started;
static bool wakeup_from_isr;
static int64_t slept_ms;

static void worker(void *a, void *b, void *c)
{
	int64_t start;

	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	start = k_uptime_get();
	sleep_started = true;
	k_sem_give(&ready);
	k_sleep(K_MSEC(SLEEP_MS));
	slept_ms = k_uptime_get() - start;
	k_sem_give(&done);
}

static void wake_worker(const void *arg)
{
	wakeup_from_isr = k_is_in_isr();
	k_wakeup((k_tid_t)arg);
}

ZTEST(thread_wakeup, test_wakeup_of_sleeping_thread_from_isr)
{
	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
					K_THREAD_STACK_SIZEOF(worker_stack),
					worker, NULL, NULL, NULL,
					K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready, K_MSEC(500)), 0);
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	zassert_true(sleep_started);
	zassert_equal(k_sem_count_get(&done), 0,
		      "worker completed before the ISR wakeup");

	irq_offload(wake_worker, tid);

	zassert_true(wakeup_from_isr, "wakeup did not run in an ISR");
	zassert_equal(k_sem_take(&done, K_MSEC(500)), 0,
		      "worker did not resume after wakeup");
	zassert_true(slept_ms < SLEEP_MS - 200,
		     "worker did not wake at least 200 ms early");
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
