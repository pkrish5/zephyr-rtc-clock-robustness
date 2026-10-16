#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

ZTEST(timer_periodic, test_periodic_expirations_and_stop)
{
    struct k_timer timer;

    k_timer_init(&timer, NULL, NULL);
    k_timer_start(&timer, K_MSEC(20), K_MSEC(20));

    uint32_t first = k_timer_status_sync(&timer);
    zassert_true(first > 0U, "first timer synchronization must report an expiry");

    uint32_t second = k_timer_status_sync(&timer);
    zassert_true(second > 0U, "second timer synchronization must report an expiry");
    zassert_true(k_timer_remaining_get(&timer) > 0 || k_timer_status_get(&timer) > 0U,
                 "timer should remain active after periodic expirations");

    k_timer_stop(&timer);
    zassert_equal(k_timer_status_sync(&timer), 0U,
                  "stopped timer must not report a further expiry");
}

ZTEST_SUITE(timer_periodic, NULL, NULL, NULL, NULL, NULL);
