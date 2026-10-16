#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <errno.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem completed;
static atomic_t worker_state;
static atomic_t expiry_in_isr;
static uint32_t received_status;

enum { INITIAL, WAITING, FINISHED };

static void timer_expired(struct k_timer *expired_timer)
{
	ARG_UNUSED(expired_timer);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : -1);
}

static void worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_timer_start(&timer, K_MSEC(1000), K_NO_WAIT);
	atomic_set(&worker_state, WAITING);
	k_sem_give(&ready);

	/* Cooperative scheduling on one CPU prevents the test thread from
	 * running between the ready signal and this blocking call.
	 */
	received_status = k_timer_status_sync(&timer);
	atomic_set(&worker_state, FINISHED);
	k_sem_give(&completed);
}

ZTEST(timer_wait, test_one_shot_wakes_pending_worker)
{
	k_sem_init(&ready, 0, 1);
	k_sem_init(&completed, 0, 1);
	k_timer_init(&timer, timer_expired, NULL);
	atomic_set(&worker_state, INITIAL);
	atomic_set(&expiry_in_isr, 0);
	received_status = 0;

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack),
				     worker, NULL, NULL, NULL,
				     K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&ready, K_MSEC(2000)),
		   "Worker did not reach the timer wait");
	zassert_equal(atomic_get(&worker_state), WAITING,
		      "Worker returned before pending was observed");
	zassert_true(k_timer_remaining_ticks(&timer) > 0,
		     "Timer already expired before pending check");
	zassert_equal(atomic_get(&expiry_in_isr), 0,
		      "Expiry callback ran before pending check");
	zassert_equal(k_sem_take(&completed, K_NO_WAIT), -EBUSY,
		      "Completion was signaled before expiry");

	zassert_ok(k_sem_take(&completed, K_MSEC(2000)),
		   "Timer expiry did not produce completion");
	zassert_equal(received_status, 1,
		      "Expected exactly one timer expiration");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback did not execute in interrupt context");
	zassert_equal(atomic_get(&worker_state), FINISHED,
		      "Worker did not finish its timer wait");
	zassert_ok(k_thread_join(tid, K_MSEC(1000)),
		   "Worker did not terminate");
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
