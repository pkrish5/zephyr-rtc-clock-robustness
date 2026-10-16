#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

static struct k_timer periodic_timer;
static atomic_t expiry_calls;

static void timer_expiry(struct k_timer *timer)
{
    (void)timer;
    atomic_inc(&expiry_calls);
}

ZTEST(periodic_timer, test_expiry_and_stop)
{
    atomic_set(&expiry_calls, 0);
    k_timer_init(&periodic_timer, timer_expiry, NULL);
    k_timer_start(&periodic_timer, K_MSEC(20), K_MSEC(20));

    zassert_true(k_timer_status_sync(&periodic_timer) > 0,
                 "first synchronization reported no expiry");
    zassert_true(k_timer_status_sync(&periodic_timer) > 0,
                 "second synchronization reported no expiry");
    zassert_true(atomic_get(&expiry_calls) >= 2,
                 "expiry callback ran fewer than twice");

    k_timer_stop(&periodic_timer);
    (void)k_timer_status_get(&periodic_timer); /* Discard any expiry pending at stop. */
    zassert_equal(k_timer_status_sync(&periodic_timer), 0,
                  "stopped timer reported another expiry");
}

ZTEST_SUITE(periodic_timer, NULL, NULL, NULL, NULL, NULL);
