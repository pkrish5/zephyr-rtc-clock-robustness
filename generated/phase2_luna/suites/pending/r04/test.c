#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)

static struct k_timer test_timer;
static struct k_sem completion_sem;
static struct k_thread worker_thread;
K_THREAD_STACK_DEFINE(worker_stack, 1024);

static volatile bool worker_started;
static volatile bool worker_blocked;
static volatile int timer_status;
static volatile int completion_status;

static void timer_worker(void *a, void *b, void *c)
{
    ARG_UNUSED(a);
    ARG_UNUSED(b);
    ARG_UNUSED(c);

    worker_started = true;
    worker_blocked = true;
    timer_status = k_timer_status_sync(&test_timer);
    worker_blocked = false;
    completion_status = k_sem_give(&completion_sem);
}

ZTEST(timer_interrupt, test_one_shot_expiry_wakes_blocked_thread)
{
    worker_started = false;
    worker_blocked = false;
    timer_status = -1;
    completion_status = -1;
    k_sem_init(&completion_sem, 0, 1);
    k_timer_init(&test_timer, NULL, NULL);

    k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
                    timer_worker, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
    k_thread_name_set(&worker_thread, "timer_worker");

    /* Let the worker reach status_sync, then verify no timer status exists yet. */
    k_sleep(K_MSEC(10));
    zassert_true(worker_started, "worker did not start");
    zassert_true(worker_blocked, "worker was not blocked awaiting the timer");
    zassert_equal(k_timer_status_get(&test_timer), 0,
                  "timer expired before it was started");
    zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
                  "completion was signaled before expiry");

    k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
    zassert_ok(k_sem_take(&completion_sem, K_SECONDS(1)),
               "timer expiry did not signal completion");

    zassert_equal(timer_status, 1, "worker did not receive timer expiration status");
    zassert_equal(completion_status, 0, "completion signal was not given");
    zassert_false(worker_blocked, "worker remained blocked after timer expiry");
    zassert_equal(k_timer_status_get(&test_timer), 0,
                  "timer expiration status was not consumed by the worker");

    k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
