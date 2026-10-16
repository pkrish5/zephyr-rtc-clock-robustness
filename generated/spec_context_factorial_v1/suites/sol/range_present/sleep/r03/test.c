#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP K_SECONDS(2)
#define EARLY_LIMIT_MS 1500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static K_SEM_DEFINE(sleep_started, 0, 1);
static K_SEM_DEFINE(sleep_done, 0, 1);
static volatile bool wake_called_in_isr;
static int64_t elapsed_ms;

static void sleeper(void *a, void *b, void *c)
{
    int64_t start_ms = k_uptime_get();

    k_sem_give(&sleep_started);
    k_sleep(REQUESTED_SLEEP);
    elapsed_ms = k_uptime_get() - start_ms;
    k_sem_give(&sleep_done);
}

static void wake_from_isr(const void *arg)
{
    wake_called_in_isr = k_is_in_isr();
    k_wakeup((struct k_thread *)arg);
}

ZTEST(thread_wakeup, test_wakeup_interrupts_sleep)
{
    k_thread_create(&sleeper_thread, sleeper_stack,
                    K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
                    NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

    zassert_ok(k_sem_take(&sleep_started, K_SECONDS(1)));
    /* Let the worker enter k_sleep even if the signal preempted it. */
    k_sleep(K_MSEC(50));
    zassert_not_equal(k_sem_take(&sleep_done, K_NO_WAIT), 0);

    irq_offload(wake_from_isr, &sleeper_thread);

    zassert_true(wake_called_in_isr);
    zassert_ok(k_sem_take(&sleep_done, K_SECONDS(1)));
    /* The 500 ms gap makes an early return clear despite tick rounding. */
    zassert_true(elapsed_ms < EARLY_LIMIT_MS);
}

ZTEST_SUITE(thread_wakeup, NULL, NULL, NULL, NULL, NULL);
