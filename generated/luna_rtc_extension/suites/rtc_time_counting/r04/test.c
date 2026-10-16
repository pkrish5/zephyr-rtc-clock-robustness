#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVATION_BOUND_MS 30000
#define RTC_POLL_INTERVAL_MS 100

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time initial = {
        .tm_sec = 50,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124,
        .tm_wday = -1,
        .tm_yday = -1,
        .tm_isdst = -1,
    };
    struct rtc_time previous;
    struct rtc_time current;
    int64_t initial_seconds;
    int64_t previous_seconds;
    int64_t current_seconds;
    int64_t target_seconds;
    int64_t deadline;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");

    zassert_equal(rtc_set_time(rtc, &initial), 0,
                  "Setting initial RTC calendar failed");
    zassert_equal(rtc_get_time(rtc, &current), 0,
                  "Reading initial RTC calendar failed");
    zassert_equal(current.tm_year, initial.tm_year, "Initial year mismatch");
    zassert_equal(current.tm_mon, initial.tm_mon, "Initial month mismatch");
    zassert_equal(current.tm_mday, initial.tm_mday, "Initial day mismatch");
    zassert_equal(current.tm_hour, initial.tm_hour, "Initial hour mismatch");
    zassert_equal(current.tm_min, initial.tm_min, "Initial minute mismatch");
    zassert_true(current.tm_sec >= initial.tm_sec && current.tm_sec <= 59,
                 "Initial seconds are out of range");

    initial_seconds = timeutil_timegm(&current);
    previous = current;
    previous_seconds = initial_seconds;
    target_seconds = initial_seconds + 10;
    deadline = k_uptime_get() + RTC_OBSERVATION_BOUND_MS;

    while (k_uptime_get() < deadline) {
        k_sleep(K_MSEC(RTC_POLL_INTERVAL_MS));
        zassert_equal(rtc_get_time(rtc, &current), 0,
                      "Reading RTC calendar failed during observation");
        current_seconds = timeutil_timegm(&current);
        zassert_true(current_seconds >= previous_seconds,
                     "RTC calendar moved backward");
        previous = current;
        previous_seconds = current_seconds;
        if (current_seconds >= target_seconds) {
            break;
        }
    }

    zassert_true(previous_seconds >= target_seconds,
                 "RTC did not advance ten calendar seconds within 30 seconds");
    zassert_true(timeutil_timegm(&previous) >= target_seconds,
                 "RTC calendar failed to reach the target time");
    zassert_true(previous.tm_year > initial.tm_year,
                 "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
