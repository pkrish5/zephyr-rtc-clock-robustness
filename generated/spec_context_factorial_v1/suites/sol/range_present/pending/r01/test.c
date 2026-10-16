#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem ready;
static struct k_sem completed;
static uint32_t received_status;

static void timer_worker(void *arg1, void *arg2, void *arg3)
{
    ARG_UNUSED(arg1);
    ARG_UNUSED(arg2);
    ARG_UNUSED(arg3);

    k_sem_give(&ready);
    received_status = k_timer_status_sync(&timer);
    k_sem_give(&completed);
}

ZTEST(timer_expiry, test_blocked_thread_receives_expiry)
{
    k_timer_init(&timer, NULL, NULL);
    k_sem_init(&ready, 0, 1);
    k_sem_init(&completed, 0, 1);
    received_status = 0;

    k_timer_start(&timer, K_MSEC(500), K_NO_WAIT);
    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
                    NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

    zassert_ok(k_sem_take(&ready, K_MSEC(100)));
    /* The cooperative worker runs through status_sync before this thread resumes. */
    zassert_true(k_timer_remaining_get(&timer) > 0);
    zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);
    zassert_equal(received_status, 0U);

    zassert_ok(k_sem_take(&completed, K_SECONDS(2)));
    zassert_equal(received_status, 1U);
    zassert_ok(k_thread_join(&worker_thread, K_NO_WAIT));
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
