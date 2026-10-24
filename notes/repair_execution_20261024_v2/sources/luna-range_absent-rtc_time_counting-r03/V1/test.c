#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time initial = {
        .tm_sec = 50,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 126, /* 2026 */
        .tm_wday = 4,
        .tm_yday = 364,
        .tm_isdst = -1,
    };
    struct rtc_time previous;
    struct rtc_time current;
    int64_t initial_seconds;
    int64_t previous_seconds;
    int64_t current_seconds;
    bool reached = false;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");
    zassert_ok(rtc_set_time(rtc, &initial), "Failed to set initial RTC time");
    zassert_ok(rtc_get_time(rtc, &previous), "Failed to read initial RTC time");

    initial_seconds = timeutil_timegm(&initial);
    previous_seconds = timeutil_timegm(&previous);
    zassert_equal(previous_seconds, initial_seconds,
                  "Initial RTC read did not match the set calendar time");

    /* Allow up to 20 seconds for at least 10 RTC ticks, with scheduling margin. */
    for (int elapsed_ms = 0; !repair_expired(); elapsed_ms += 100) {
        k_sleep(K_MSEC(100));
        zassert_ok(rtc_get_time(rtc, &current), "Failed to read RTC time");
        current_seconds = timeutil_timegm(&current);
        zassert_true(current_seconds >= previous_seconds,
                     "RTC calendar moved backward");
        previous_seconds = current_seconds;
        if (current_seconds >= initial_seconds + 10) {
            reached = true;
            break;
        }
    }

    zassert_true(reached, "RTC did not advance by 10 seconds within 20 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
