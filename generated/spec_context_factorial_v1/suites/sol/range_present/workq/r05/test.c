#include <errno.h>
#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define DELAY_MS 50

K_SEM_DEFINE(completion, 0, 2);
static atomic_t run_count;
static int64_t handler_time;

static void delayed_handler(struct k_work *work)
{
    ARG_UNUSED(work);
    handler_time = k_uptime_get();
    atomic_inc(&run_count);
    k_sem_give(&completion);
}

K_WORK_DELAYABLE_DEFINE(delayed_work, delayed_handler);

ZTEST(delayed_work, runs_once_after_delay)
{
    int64_t scheduled_at = k_uptime_get();

    zassert_equal(k_work_schedule(&delayed_work, K_MSEC(DELAY_MS)), 1);
    zassert_true(k_work_delayable_is_pending(&delayed_work));

    zassert_equal(k_sem_take(&completion, K_MSEC(500)), 0);
    zassert_true(handler_time - scheduled_at >=
                 DELAY_MS - k_ticks_to_ms_ceil64(1));
    zassert_false(k_work_delayable_is_pending(&delayed_work));

    zassert_equal(k_sem_take(&completion, K_MSEC(DELAY_MS)), -EAGAIN);
    zassert_equal(atomic_get(&run_count), 1);
}

ZTEST_SUITE(delayed_work, NULL, NULL, NULL, NULL, NULL);
