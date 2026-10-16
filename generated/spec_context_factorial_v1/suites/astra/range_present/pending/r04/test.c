#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem entering_wait;
static struct k_sem completed;
static atomic_t expiry_count;
static atomic_t expiry_in_isr;
static uint32_t received_status;

static void timer_expired(struct k_timer *unused)
{
	ARG_UNUSED(unused);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : 0);
	atomic_inc(&expiry_count);
}

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, K_MSEC(250), K_NO_WAIT);
	k_sem_give(&entering_wait);
	/* No yield between announcing the wait and actually blocking. */
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&completed);
}

ZTEST(timer_delivery, test_one_shot_wakes_pending_worker)
{
	int ready_rc;
	int early_completion_rc;
	int completion_rc;
	int join_rc;
	atomic_val_t early_expiries;
	k_ticks_t remaining;

	k_sem_init(&entering_wait, 0, 1);
	k_sem_init(&completed, 0, 1);
	atomic_set(&expiry_count, 0);
	atomic_set(&expiry_in_isr, 0);
	received_status = UINT32_MAX;
	k_timer_init(&timer, timer_expired, NULL);

	/*
	 * On this single CPU, the cooperative worker cannot be preempted
	 * by the test after giving entering_wait. Once the test runs again,
	 * it has either blocked in status_sync or already completed.
	 * Checking both expiry and completion distinguishes these cases.
	 */
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	ready_rc = k_sem_take(&entering_wait, K_SECONDS(3));
	early_completion_rc = k_sem_take(&completed, K_NO_WAIT);
	early_expiries = atomic_get(&expiry_count);
	remaining = k_timer_remaining_ticks(&timer);

	/* These are watchdog timeouts, not ISR delivery-latency bounds. */
	completion_rc = k_sem_take(&completed, K_SECONDS(3));
	join_rc = k_thread_join(&worker_thread, K_SECONDS(3));
	if (join_rc != 0) {
		k_thread_abort(&worker_thread);
	}
	k_timer_stop(&timer);

	zassert_equal(ready_rc, 0, "Worker did not reach timer wait");
	zassert_equal(early_completion_rc, -EBUSY,
		      "Worker completed before pending check");
	zassert_equal(early_expiries, 0,
		      "Timer expired before pending check");
	zassert_true(remaining > 0, "Timer was not pending");
	zassert_equal(completion_rc, 0, "Completion signal was lost");
	zassert_equal(join_rc, 0, "Worker failed to exit");
	zassert_equal(received_status, 1,
		      "Expected exactly one received timer expiration");
	zassert_equal(atomic_get(&expiry_count), 1,
		      "Expected exactly one expiry callback");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback did not run in interrupt context");
}

ZTEST_SUITE(timer_delivery, NULL, NULL, NULL, NULL, NULL);
