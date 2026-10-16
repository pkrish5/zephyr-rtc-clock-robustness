#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

#define WORKER_STACK_SIZE 1024

K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem entering_wait;
static struct k_sem completed;
static atomic_t phase;
static atomic_t expirations;
static atomic_t expired_in_isr;
static uint32_t received_status;
static bool worker_created;

static void timer_expired(struct k_timer *unused)
{
	ARG_UNUSED(unused);
	atomic_set(&expired_in_isr, k_is_in_isr() ? 1 : 0);
	atomic_inc(&expirations);
}

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_timer_start(&timer, K_MSEC(100), K_NO_WAIT);
	atomic_set(&phase, 1);
	k_sem_give(&entering_wait);

	/* No scheduling point between the announcement and this wait. */
	received_status = k_timer_status_sync(&timer);
	atomic_set(&phase, 2);
	k_sem_give(&completed);
}

static void cleanup(void *fixture)
{
	ARG_UNUSED(fixture);
	if (worker_created) {
		k_thread_abort(&worker_thread);
		worker_created = false;
	}
	k_timer_stop(&timer);
}

ZTEST(timer_interrupt_delivery, test_pending_wait_receives_expiration)
{
	k_sem_init(&entering_wait, 0, 1);
	k_sem_init(&completed, 0, 1);
	k_timer_init(&timer, timer_expired, NULL);
	atomic_clear(&phase);
	atomic_clear(&expirations);
	atomic_clear(&expired_in_isr);
	received_status = 0;

	/* On this single CPU, a cooperative worker runs until it blocks. */
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);
	worker_created = true;

	/* These timeouts are test watchdogs, not clock-derived latency bounds. */
	zassert_equal(k_sem_take(&entering_wait, K_SECONDS(2)), 0,
		      "Worker did not reach the timer wait");

	/*
	 * The worker cannot be preempted by this test thread. After its
	 * announcement, it can relinquish the CPU only by blocking in
	 * status_sync or by finishing. Snapshot under IRQ lock so expiry
	 * cannot race the checks establishing the pre-expiry blocked state.
	 */
	unsigned int key = irq_lock();
	atomic_val_t observed_phase = atomic_get(&phase);
	atomic_val_t observed_expirations = atomic_get(&expirations);
	unsigned int observed_completion = k_sem_count_get(&completed);
	irq_unlock(key);

	zassert_equal(observed_phase, 1, "Worker was not pending");
	zassert_equal(observed_expirations, 0,
		      "Timer expired before pending state was observed");
	zassert_equal(observed_completion, 0, "Worker completed prematurely");

	/* A completion posted before this take must remain available. */
	zassert_equal(k_sem_take(&completed, K_SECONDS(2)), 0,
		      "Timer wakeup or completion signal was lost");
	zassert_equal(received_status, 1, "Expected one timer expiration");
	zassert_equal(atomic_get(&phase), 2, "Worker did not finish its wait");
	zassert_equal(atomic_get(&expirations), 1,
		      "Expected exactly one expiry callback");
	zassert_equal(atomic_get(&expired_in_isr), 1,
		      "Expiry callback did not execute in interrupt context");
	zassert_equal(k_timer_status_get(&timer), 0,
		      "status_sync did not consume the expiration");
}

ZTEST_SUITE(timer_interrupt_delivery, NULL, NULL, NULL, cleanup, NULL);
