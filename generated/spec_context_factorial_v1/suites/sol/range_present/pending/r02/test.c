#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);

static struct k_thread worker_thread;
static struct k_timer timer;
static struct k_sem entered_wait;
static struct k_sem completed;
static uint32_t received_status;

static void timer_worker(void *a, void *b, void *c)
{
    k_sem_give(&entered_wait);
    received_status = k_timer_status_sync(&timer);
    k_sem_give(&completed);
}

ZTEST(timer_wait, test_one_shot_expiry_wakes_worker)
{
    received_status = 0;
    k_sem_init(&entered_wait, 0, 1);
    k_sem_init(&completed, 0, 1);
    k_timer_init(&timer, NULL, NULL);
    k_timer_start(&timer, K_MSEC(500), K_NO_WAIT);

    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
                    NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

    zassert_ok(k_sem_take(&entered_wait, K_MSEC(300)));
    /* The cooperative worker yielded the CPU by blocking in status_sync. */
    zassert_true(k_timer_remaining_get(&timer) > 0);
    zassert_not_equal(k_sem_take(&completed, K_NO_WAIT), 0);

    zassert_ok(k_sem_take(&completed, K_MSEC(3000)));
    zassert_equal(received_status, 1);
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
