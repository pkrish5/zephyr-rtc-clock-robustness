#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define TIMER_PERIOD K_MSEC(20)
#define OBSERVE_TIME K_MSEC(10)

static struct k_timer periodic_timer;
static atomic_t expiry_count;

static void timer_expiry(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    atomic_inc(&expiry_count);
}

ZTEST(timer_expiry, test_periodic_timer_expirations_and_stop)
{
    atomic_set(&expiry_count, 0);
    k_timer_init(&periodic_timer, timer_expiry, NULL);
    k_timer_start(&periodic_timer, TIMER_PERIOD, TIMER_PERIOD);

    uint32_t first = k_timer_status_sync(&periodic_timer);
    zassert_true(first > 0U, "first synchronization must report an expiry");

    uint32_t second = k_timer_status_sync(&periodic_timer);
    zassert_true(second > 0U, "second synchronization must report an expiry");
    zassert_true(atomic_get(&expiry_count) >= 2,
                 "expiry callback should have run at least twice");
    zassert_true(k_timer_remaining_get(&periodic_timer) > 0,
                 "periodic timer should remain active");

    k_timer_stop(&periodic_timer);
    int stopped_count = atomic_get(&expiry_count);
    k_sleep(OBSERVE_TIME);

    zassert_equal(k_timer_status_get(&periodic_timer), 0,
                  "stopped timer must have no pending expiry status");
    zassert_equal(atomic_get(&expiry_count), stopped_count,
                  "expiry callback count must remain stable after stop");
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
