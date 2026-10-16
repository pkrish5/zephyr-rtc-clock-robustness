#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP_MS 2000
#define EARLY_WAKE_LIMIT_MS 1500

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker;
static struct k_sem started;
static struct k_sem done;
static atomic_t sleep_entered;
static atomic_t finished;
static atomic_t callback_in_isr;
static atomic_t callback_saw_pending_sleep;
static int64_t elapsed_ms;

static void sleeping_worker(void *a, void *b, void *c)
{
	int64_t start_ms = k_uptime_get();

	atomic_set(&sleep_entered, 1);
	k_sem_give(&started);
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	elapsed_ms = k_uptime_get() - start_ms;
	atomic_set(&finished, 1);
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	atomic_set(&callback_in_isr, k_is_in_isr());
	atomic_set(&callback_saw_pending_sleep,
		   atomic_get(&sleep_entered) && !atomic_get(&finished));
	k_wakeup(&worker);
}

ZTEST(thread_wakeup, test_isr_wakes_sleeping_thread)
{
	k_sem_init(&started, 0, 1);
	k_sem_init(&done, 0, 1);

	k_thread_create(&worker, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
			sleeping_worker, NULL, NULL, NULL,
			K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&started, K_SECONDS(1)), "worker did not start");
	/* The worker signals immediately before sleeping. Give it time to enter k_sleep(). */
	k_sleep(K_MSEC(100));
	irq_offload(wake_from_isr, NULL);

	zassert_true(atomic_get(&callback_in_isr), "wakeup was not issued from an ISR");
	zassert_true(atomic_get(&callback_saw_pending_sleep),
		     "worker had not entered its sleep path or had already finished");
	zassert_ok(k_sem_take(&done, K_SECONDS(1)), "worker did not complete after wakeup");
	zassert_true(atomic_get(&finished), "worker did not report completion");
	zassert_true(elapsed_ms < EARLY_WAKE_LIMIT_MS,
		     "worker did not wake at least 500 ms before the 2000 ms deadline");
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
