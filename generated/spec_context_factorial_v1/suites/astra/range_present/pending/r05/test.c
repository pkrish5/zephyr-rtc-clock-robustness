#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>

#define EXPIRY_DELAY K_MSEC(100)
/* Test watchdog only; not an ISR-to-thread latency specification. */
#define WATCHDOG K_MSEC(2000)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem completed;
static atomic_t expiry_count;
static atomic_t expiry_in_isr;
static atomic_t received_status;

static void on_expiry(struct k_timer *expired)
{
	ARG_UNUSED(expired);
	atomic_set(&expiry_in_isr, k_is_in_isr());
	atomic_inc(&expiry_count);
}

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, EXPIRY_DELAY, K_NO_WAIT);
	k_sem_give(&ready);
	atomic_set(&received_status, k_timer_status_sync(&timer));
	k_sem_give(&completed);
}

ZTEST(timer_delivery, test_pending_thread_receives_one_shot)
{
	int original_priority = k_thread_priority_get(k_current_get());
	int ready_rc;
	int completion_before;
	int completion_rc;
	int join_rc;
	atomic_val_t expiries_before;
	atomic_val_t status_before;

	k_sem_init(&ready, 0, 1);
	k_sem_init(&completed, 0, 1);
	atomic_set(&expiry_count, 0);
	atomic_set(&expiry_in_isr, 0);
	atomic_set(&received_status, -1);
	k_timer_init(&timer, on_expiry, NULL);

	/*
	 * On this single CPU, the cooperative worker outranks this test
	 * thread. After signaling ready it cannot yield execution to us
	 * until status_sync blocks (or it completes). Checking that expiry
	 * and completion have not happened therefore establishes pending.
	 */
	k_thread_priority_set(k_current_get(), K_PRIO_PREEMPT(0));
	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	ready_rc = k_sem_take(&ready, WATCHDOG);
	status_before = atomic_get(&received_status);
	completion_before = k_sem_take(&completed, K_NO_WAIT);
	expiries_before = atomic_get(&expiry_count);

	completion_rc = completion_before == 0 ? 0 :
		k_sem_take(&completed, WATCHDOG);
	join_rc = k_thread_join(&worker_thread, WATCHDOG);
	if (join_rc != 0) {
		k_thread_abort(&worker_thread);
	}
	k_timer_stop(&timer);
	k_thread_priority_set(k_current_get(), original_priority);

	/* Assert after cleanup so failures leave no live worker or timer. */
	zassert_equal(ready_rc, 0, "Worker did not reach timer wait");
	zassert_equal(status_before, -1, "Timer wait returned prematurely");
	zassert_equal(completion_before, -EBUSY,
		      "Worker completed before pending observation");
	zassert_equal(expiries_before, 0,
		      "Timer expired before pending observation");
	zassert_equal(completion_rc, 0, "Completion signal was not received");
	zassert_equal(join_rc, 0, "Worker did not exit");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback did not execute in interrupt context");
	zassert_equal(atomic_get(&expiry_count), 1,
		      "Expected exactly one one-shot expiry");
	zassert_equal(atomic_get(&received_status), 1,
		      "Worker did not receive exactly one timer expiration");
}

ZTEST_SUITE(timer_delivery, NULL, NULL, NULL, NULL, NULL);
