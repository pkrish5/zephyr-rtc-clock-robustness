#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(200)

static struct k_timer periodic_timer;
static atomic_t expiry_callback_count;
static struct k_sem sync_started;
static struct k_sem sync_finished;
static uint32_t stopped_sync_status;

static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	atomic_inc(&expiry_callback_count);
}

static void stopped_sync_thread(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&sync_started);
	stopped_sync_status = k_timer_status_sync(&periodic_timer);
	k_sem_give(&sync_finished);
}

K_THREAD_STACK_DEFINE(stopped_sync_stack, 1024);
static struct k_thread stopped_sync_thread_data;

ZTEST(timer_interrupt, test_periodic_timer_expirations_and_stop)
{
	atomic_set(&expiry_callback_count, 0);
	k_timer_init(&periodic_timer, timer_expiry_fn, NULL);
	k_sem_init(&sync_started, 0, 1);
	k_sem_init(&sync_finished, 0, 1);

	k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

	uint32_t first = k_timer_status_sync(&periodic_timer);
	uint32_t second = k_timer_status_sync(&periodic_timer);

	zassert_true(first > 0U, "first timer synchronization reported no expiry");
	zassert_true(second > 0U, "second timer synchronization reported no expiry");
	zassert_true(atomic_get(&expiry_callback_count) >= 2,
		     "expiry callback count did not reach two");

	k_thread_create(&stopped_sync_thread_data, stopped_sync_stack,
			K_THREAD_STACK_SIZEOF(stopped_sync_stack), stopped_sync_thread,
			NULL, NULL, NULL, K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	zassert_equal(k_sem_take(&sync_started, K_SECONDS(1)), 0,
		      "sync worker did not start");

	k_timer_stop(&periodic_timer);
	zassert_equal(k_sem_take(&sync_finished, K_SECONDS(1)), 0,
		      "sync worker did not return after timer stop");
	zassert_equal(stopped_sync_status, 0U,
		      "synchronization reported an expiry after timer stop");
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
