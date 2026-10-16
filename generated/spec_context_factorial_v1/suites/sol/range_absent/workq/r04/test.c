#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/atomic.h>

#define DELAY_MS 100

K_SEM_DEFINE(work_done, 0, 2);
static atomic_t run_count = ATOMIC_INIT(0);
static int64_t run_time_ms;

static void delayed_handler(struct k_work *work)
{
    ARG_UNUSED(work);
    run_time_ms = k_uptime_get();
    atomic_inc(&run_count);
    k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work, test_system_queue_delay)
{
    int64_t start_ms = k_uptime_get();
    int64_t tick_tolerance_ms =
        (1000 + CONFIG_SYS_CLOCK_TICKS_PER_SEC - 1) /
        CONFIG_SYS_CLOCK_TICKS_PER_SEC + 1;

    zassert_equal(k_work_schedule(&delayed_work, K_MSEC(DELAY_MS)), 1);
    zassert_true(k_work_delayable_is_pending(&delayed_work));

    zassert_not_equal(k_sem_take(&work_done, K_MSEC(20)), 0);
    zassert_equal(atomic_get(&run_count), 0);
    zassert_true(k_work_delayable_is_pending(&delayed_work));

    zassert_ok(k_sem_take(&work_done, K_MSEC(2000)));
    zassert_equal(atomic_get(&run_count), 1);
    zassert_true(run_time_ms - start_ms >= DELAY_MS - tick_tolerance_ms);
    zassert_false(k_work_delayable_is_pending(&delayed_work));

    zassert_not_equal(k_sem_take(&work_done, K_MSEC(150)), 0);
    zassert_equal(atomic_get(&run_count), 1);
}

ZTEST_SUITE(delayed_work, NULL, NULL, NULL, NULL, NULL);