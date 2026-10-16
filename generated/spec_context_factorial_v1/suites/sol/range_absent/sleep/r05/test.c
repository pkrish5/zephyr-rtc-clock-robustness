#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(ready_sem, 0, 1);
K_SEM_DEFINE(done_sem, 0, 1);

static struct k_thread worker_thread;
static atomic_t sleep_started;
static atomic_t wakeup_from_isr;
static int64_t elapsed_ms;

static void sleeper(void *a, void *b, void *c)
{
	int64_t start_ms = k_uptime_get();

	atomic_set(&sleep_started, 1);
	k_sem_give(&ready_sem);
	k_sleep(REQUESTED_SLEEP);
	elapsed_ms = k_uptime_get() - start_ms;
	k_sem_give(&done_sem);
}

static void wakeup_isr(const void *arg)
{
	ARG_UNUSED(arg);
	atomic_set(&wakeup_from_isr,
		   k_is_in_isr() && atomic_get(&sleep_started));
	k_wakeup(&worker_thread);
}

ZTEST(thread_wakeup, test_wakeup_sleeping_thread_from_isr)
{
	atomic_set(&sleep_started, 0);
	atomic_set(&wakeup_from_isr, 0);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready_sem, K_SECONDS(1)), 0,
		      "sleeper did not start");
	/* Let the worker enter its two-second sleep after signaling readiness. */
	k_sleep(K_MSEC(100));

	irq_offload(wakeup_isr, NULL);

	zassert_equal(k_sem_take(&done_sem, K_MSEC(500)), 0,
		      "sleeper did not report completion after wakeup");
	zassert_true(atomic_get(&wakeup_from_isr),
		     "wakeup was not issued from ISR after sleep began");
	zassert_true(elapsed_ms < 1000,
		     "observed sleep was not at least one second shorter than requested");
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
