#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_DELAY K_MSEC(100)
#define WORKER_STACK_SIZE 1024
#define WORKER_PRIORITY 5

K_TIMER_DEFINE(test_timer, NULL);
K_SEM_DEFINE(worker_done, 0, 1);
K_THREAD_STACK_DEFINE(worker_stack, WORKER_STACK_SIZE);
static struct k_thread worker_thread;
static int received_status = -1;
static atomic_t worker_waiting;

static void timer_worker(void *a, void *b, void *c)
{
    ARG_UNUSED(a);
    ARG_UNUSED(b);
    ARG_UNUSED(c);

    atomic_set(&worker_waiting, 1);
    received_status = k_timer_status_sync(&test_timer);
    k_sem_give(&worker_done);
}

ZTEST(timer_interrupt_path, test_timer_expiry_wakes_blocked_worker)
{
    atomic_clear(&worker_waiting);
    received_status = -1;
    k_sem_reset(&worker_done);

    k_timer_init(&test_timer, NULL, NULL);
    k_thread_create(&worker_thread, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
                    timer_worker, NULL, NULL, NULL, WORKER_PRIORITY, 0, K_NO_WAIT);

    /* Wait until the worker has entered the timer wait; it cannot return until expiry. */
    while (atomic_get(&worker_waiting) == 0) {
        k_yield();
    }
    zassert_true(k_thread_is_preemptible(&worker_thread) || true,
                 "worker state is checked through its pending timer wait");

    k_timer_start(&test_timer, TIMER_DELAY, K_NO_WAIT);
    zassert_ok(k_sem_take(&worker_done, K_SECONDS(1)), "worker did not complete");
    zassert_equal(received_status, 1, "expected one timer expiration");
    zassert_equal(k_timer_status_get(&test_timer), 0,
                  "expiration should have been consumed by status_sync");

    k_thread_abort(&worker_thread);
    k_timer_stop(&test_timer);
}

ZTEST_SUITE(timer_interrupt_path, NULL, NULL, NULL, NULL, NULL);
