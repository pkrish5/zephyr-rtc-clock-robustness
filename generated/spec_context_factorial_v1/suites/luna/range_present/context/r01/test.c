#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define SLEEP_INTERVAL K_MSEC(250)
#define COMPLETION_WAIT K_SECONDS(2)

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem entered_sem;
static struct k_sem unrelated_sem;
static struct k_sem completion_sem;
static int64_t sleep_start_ms;
static int64_t sleep_elapsed_ms;

static void sleep_worker(void *a, void *b, void *c)
{
    ARG_UNUSED(a);
    ARG_UNUSED(b);
    ARG_UNUSED(c);

    k_sem_give(&entered_sem);
    k_sem_give(&unrelated_sem);
    sleep_start_ms = k_uptime_get();
    (void)k_sleep(SLEEP_INTERVAL);
    sleep_elapsed_ms = k_uptime_get() - sleep_start_ms;
    k_sem_give(&completion_sem);
}

ZTEST(timer_sleep_wakeup, test_timed_sleep_wakeup)
{
    k_sem_init(&entered_sem, 0, 1);
    k_sem_init(&unrelated_sem, 0, 1);
    k_sem_init(&completion_sem, 0, 1);

    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack), sleep_worker,
                    NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

    zassert_ok(k_sem_take(&entered_sem, K_SECONDS(1)),
               "worker did not enter its timed-sleep path");
    zassert_ok(k_sem_take(&unrelated_sem, K_NO_WAIT),
               "expected the worker's unrelated immediate signal");
    zassert_equal(k_sem_take(&completion_sem, K_NO_WAIT), -EBUSY,
                  "completion arrived before the sleep timeout");

    zassert_ok(k_sem_take(&completion_sem, COMPLETION_WAIT),
               "worker did not complete after its sleep timeout");
    zassert_true(sleep_elapsed_ms >= 250,
                 "worker resumed too early: elapsed %lld ms",
                 (long long)sleep_elapsed_ms);
}

ZTEST_SUITE(timer_sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
