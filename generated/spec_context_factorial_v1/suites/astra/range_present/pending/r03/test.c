#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem armed;
static struct k_sem completed;
static atomic_t returned;
static atomic_t expiry_count;
static atomic_t expiry_in_isr;
static uint32_t received_status;

static void on_expiry(struct k_timer *expired)
{
	ARG_UNUSED(expired);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : 0);
	atomic_inc(&expiry_count);
}

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, K_MSEC(500), K_NO_WAIT);
	k_sem_give(&armed);
	received_status = k_timer_status_sync(&timer);
	atomic_set(&returned, 1);
	k_sem_give(&completed);
}

ZTEST(timer_delivery, test_pending_worker_receives_expiration)
{
	k_sem_init(&armed, 0, 1);
	k_sem_init(&completed, 0, 1);
	k_timer_init(&timer, on_expiry, NULL);
	atomic_clear(&returned);
	atomic_clear(&expiry_count);
	atomic_clear(&expiry_in_isr);
	received_status = UINT32_MAX;

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				    K_THREAD_STACK_SIZEOF(worker_stack),
				    worker, NULL, NULL, NULL,
				    K_PRIO_COOP(0), 0, K_NO_WAIT);

	int armed_rc = k_sem_take(&armed, K_SECONDS(5));

	/*
	 * On this single CPU, the cooperative worker cannot be preempted
	 * by this test after giving 'armed'. It next blocks only in
	 * k_timer_status_sync(), or returns from that call. Thus observing
	 * 'armed', no return, and an unexpired timer proves it is blocked.
	 */
	bool not_returned = atomic_get(&returned) == 0;
	bool before_expiry = k_timer_remaining_ticks(&timer) > 0 &&
			     atomic_get(&expiry_count) == 0;
	int early_completion_rc = k_sem_take(&completed, K_NO_WAIT);

	/* This is a test watchdog, not a clock-derived delivery bound. */
	int completion_rc = early_completion_rc;
	if (early_completion_rc != 0) {
		completion_rc = k_sem_take(&completed, K_SECONDS(5));
	}

	/* Stop also releases a status_sync waiter if the watchdog failed. */
	k_timer_stop(&timer);
	int join_rc = k_thread_join(tid, K_SECONDS(1));
	if (join_rc != 0) {
		k_thread_abort(tid);
	}

	zassert_equal(armed_rc, 0, "Worker did not arm the timer");
	zassert_true(not_returned && before_expiry,
		     "Worker was not observed blocked before expiry");
	zassert_equal(early_completion_rc, -EBUSY,
		      "Completion occurred before the pending check");
	zassert_equal(completion_rc, 0, "Completion signal was lost");
	zassert_equal(join_rc, 0, "Worker did not exit");
	zassert_equal(atomic_get(&returned), 1, "Wait did not return");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiration did not execute in interrupt context");
	zassert_equal(atomic_get(&expiry_count), 1,
		      "Expected exactly one expiration");
	zassert_equal(received_status, 1,
		      "Worker did not receive one timer expiration");
	zassert_equal(k_timer_status_get(&timer), 0,
		      "Worker did not consume the expiration status");
}

ZTEST_SUITE(timer_delivery, NULL, NULL, NULL, NULL, NULL);
