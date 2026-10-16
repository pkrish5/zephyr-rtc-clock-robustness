#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define TEST_TIMEOUT K_MSEC(1000)

K_TIMER_DEFINE(test_timer, NULL, NULL);
K_SEM_DEFINE(timer_done, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static int worker_status = -1;
static atomic_t worker_started;

static void timer_worker(void *a, void *b, void *c)
{
    ARG_UNUSED(a);
    ARG_UNUSED(b);
    ARG_UNUSED(c);

    atomic_set(&worker_started, 1);
    worker_status = k_timer_status_sync(&test_timer);
    k_sem_give(&timer_done);
}

ZTEST(timer_interrupt, test_one_shot_expiration_wakes_blocked_worker)
{
    atomic_set(&worker_started, 0);
    worker_status = -1;
    k_sem_reset(&timer_done);
    k_timer_stop(&test_timer);
    k_timer_status_get(&test_timer);

    k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
                    NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

    /* Allow the worker to start and block in k_timer_status_sync(). */
    k_sleep(K_MSEC(10));
    zassert_true(atomic_get(&worker_started) != 0, "worker did not start");
    zassert_equal(k_sem_take(&timer_done, K_NO_WAIT), -EAGAIN,
                  "worker completed before timer expiry");

    zassert_ok(k_sem_take(&timer_done, TEST_TIMEOUT),
               "timer expiration did not complete worker");
    zassert_equal(worker_status, 1, "expected exactly one timer expiration");
    zassert_equal(k_timer_status_get(&test_timer), 0,
                  "timer expiration status was not consumed");

    k_thread_join(&worker_thread, TEST_TIMEOUT);
    k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt, NULL, NULL, NULL, NULL, NULL);
