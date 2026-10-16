#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define WORK_DELAY_MS 50

K_SEM_DEFINE(work_done, 0, 1);
static atomic_t run_count;
static int64_t handler_time_ms;

static void delayed_handler(struct k_work *work)
{
    ARG_UNUSED(work);
    handler_time_ms = k_uptime_get();
    atomic_inc(&run_count);
    k_sem_give(&work_done);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work, test_system_workqueue_delay)
{
    int64_t scheduled_at_ms = k_uptime_get();

    zassert_equal(k_work_schedule(&delayed_work, K_MSEC(WORK_DELAY_MS)), 1);
    zassert_true(k_work_delayable_is_pending(&delayed_work));
    zassert_equal(atomic_get(&run_count), 0);

    zassert_equal(k_sem_take(&work_done, K_MSEC(500)), 0);
    zassert_equal(atomic_get(&run_count), 1);
    zassert_true(handler_time_ms - scheduled_at_ms >=
                 WORK_DELAY_MS - k_ticks_to_ms_ceil64(1));
    zassert_false(k_work_delayable_is_pending(&delayed_work));

    k_sleep(K_MSEC(WORK_DELAY_MS));
    zassert_equal(atomic_get(&run_count), 1);
    zassert_false(k_work_delayable_is_pending(&delayed_work));
}

ZTEST_SUITE(delayed_work, NULL, NULL, NULL, NULL, NULL);
