#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

#define WORKER_STACK_SIZE 1024
#define EXPIRY_DELAY K_MSEC(250)
/* Practical test watchdog, not a latency bound derived from HSI accuracy. */
#define TEST_TIMEOUT K_SECONDS(5)

K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem complete;
static atomic_t expiry_count;
static atomic_t expiry_in_isr;
static uint32_t received_status;

static void timer_expired(struct k_timer *expired_timer)
{
	ARG_UNUSED(expired_timer);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : 0);
	atomic_inc(&expiry_count);
}

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_timer_start(&timer, EXPIRY_DELAY, K_NO_WAIT);
	k_sem_give(&ready);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&complete);
}

ZTEST(timer_interrupt_delivery, test_blocked_worker_receives_expiry)
{
	k_sem_init(&ready, 0, 1);
	k_sem_init(&complete, 0, 1);
	k_timer_init(&timer, timer_expired, NULL);
	atomic_clear(&expiry_count);
	atomic_clear(&expiry_in_isr);
	received_status = UINT32_MAX;

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
		K_THREAD_STACK_SIZEOF(worker_stack), worker,
		NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_equal(k_sem_take(&ready, TEST_TIMEOUT), 0,
		      "Worker did not start");

	/*
	 * On this single CPU, the cooperative worker cannot yield to this
	 * test between giving ready and blocking in status_sync(). It has
	 * no other blocking operation. Observing no expiry and no completion
	 * therefore establishes that it is still blocked on the timer.
	 * Lock interrupts to make the pre-expiry observations coherent.
	 */
	unsigned int key = irq_lock();
	uint32_t remaining = k_timer_remaining_get(&timer);
	atomic_val_t early_expiries = atomic_get(&expiry_count);
	int early_completion = k_sem_take(&complete, K_NO_WAIT);
	irq_unlock(key);

	zassert_true(remaining > 0, "Missed the pre-expiry observation window");
	zassert_equal(early_expiries, 0, "Timer already expired");
	zassert_equal(early_completion, -EBUSY,
		      "Worker completed before expiry");

	/* The semaphore retains completion even if expiry occurs before take. */
	zassert_equal(k_sem_take(&complete, TEST_TIMEOUT), 0,
		      "Timer expiry did not produce worker completion");
	zassert_equal(k_thread_join(tid, TEST_TIMEOUT), 0,
		      "Worker did not exit");
	zassert_equal(received_status, 1, "Expected one received expiration");
	zassert_equal(atomic_get(&expiry_count), 1,
		      "Expected one expiry callback");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback did not run in interrupt context");
	zassert_equal(k_timer_status_get(&timer), 0,
		      "Worker did not consume timer status");
	zassert_equal(k_sem_take(&complete, K_NO_WAIT), -EBUSY,
		      "Unexpected extra completion");
}

ZTEST_SUITE(timer_interrupt_delivery, NULL, NULL, NULL, NULL, NULL);
