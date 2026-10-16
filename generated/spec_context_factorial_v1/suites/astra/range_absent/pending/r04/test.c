#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem entered;
static struct k_sem completed;
static atomic_t expiry_in_isr;
static uint32_t received_status;

static void timer_expired(struct k_timer *expired)
{
	ARG_UNUSED(expired);
	atomic_set(&expiry_in_isr, k_is_in_isr() ? 1 : -1);
}

static void worker(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_timer_start(&timer, K_MSEC(200), K_NO_WAIT);
	k_sem_give(&entered);
	received_status = k_timer_status_sync(&timer);
	k_sem_give(&completed);
}

ZTEST(timer_wait, test_one_shot_wakes_pending_worker)
{
	k_sem_init(&entered, 0, 1);
	k_sem_init(&completed, 0, 1);
	atomic_clear(&expiry_in_isr);
	received_status = 0;
	k_timer_init(&timer, timer_expired, NULL);

	k_tid_t tid = k_thread_create(&worker_thread, worker_stack,
				     K_THREAD_STACK_SIZEOF(worker_stack),
				     worker, NULL, NULL, NULL,
				     K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&entered, K_SECONDS(1)),
		   "Worker did not enter timer wait");
	/*
	 * On this single CPU, the cooperative worker cannot yield to this
	 * thread at k_sem_give(). It must reach the blocking status_sync()
	 * before this thread resumes. Remaining time confirms no expiry yet.
	 */
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "Timer expired before the pending check");
	zassert_equal(atomic_get(&expiry_in_isr), 0,
		      "Expiry callback ran before the pending check");
	zassert_true(k_sem_take(&completed, K_NO_WAIT) != 0,
		     "Worker completed before timer expiry");

	zassert_ok(k_sem_take(&completed, K_SECONDS(2)),
		   "Timer wakeup or completion signal was lost");
	zassert_ok(k_thread_join(tid, K_SECONDS(1)),
		   "Worker did not terminate");
	zassert_equal(received_status, 1,
		      "Worker must receive exactly one expiration");
	zassert_equal(atomic_get(&expiry_in_isr), 1,
		      "Expiry callback must run in interrupt context");
	zassert_equal(k_timer_status_get(&timer), 0,
		      "Worker must consume the expiration status");
	k_timer_stop(&timer);
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
