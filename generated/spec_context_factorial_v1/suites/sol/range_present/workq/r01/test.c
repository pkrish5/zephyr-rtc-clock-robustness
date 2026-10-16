#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define WORK_DELAY_MS 50

K_SEM_DEFINE(work_done, 0, 1);

static atomic_t handler_runs;
static int64_t handler_tick;

static void delayed_work_handler(struct k_work *work)
{
    ARG_UNUSED(work);
    handler_tick = k_uptime_ticks();
    atomic_inc(&handler_runs);
    k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_work_handler);

ZTEST(delayable_work, test_system_queue_delay)
{
    int64_t start_tick = k_uptime_ticks();

    zassert_equal(k_work_schedule(&delayed_work, K_MSEC(WORK_DELAY_MS)), 1);
    zassert_true(k_work_delayable_is_pending(&delayed_work));
    zassert_equal(atomic_get(&handler_runs), 0);

    zassert_ok(k_sem_take(&work_done, K_MSEC(1000)));
    zassert_equal(atomic_get(&handler_runs), 1);
    zassert_true(handler_tick - start_tick >=
                 (int64_t)k_ms_to_ticks_ceil64(WORK_DELAY_MS) - 1,
                 "handler ran before the delay, allowing one tick of granularity");
    zassert_false(k_work_delayable_is_pending(&delayed_work));
}

ZTEST_SUITE(delayable_work, NULL, NULL, NULL, NULL, NULL);
