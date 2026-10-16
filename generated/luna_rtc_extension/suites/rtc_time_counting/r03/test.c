#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVATION_BOUND_SECONDS 18
#define RTC_POLL_INTERVAL_MS 200

ZTEST(rtc_calendar, test_calendar_advances_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    zassert_true(device_is_ready(rtc), "RTC device is not ready");

    struct rtc_time initial = {
        .tm_sec = 55,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124, /* 2024 */
        .tm_wday = 2,
        .tm_yday = 365,
        .tm_isdst = -1,
    };
    zassert_equal(rtc_set_time(rtc, &initial), 0, "Failed to set RTC calendar");

    struct rtc_time readback;
    zassert_equal(rtc_get_time(rtc, &readback), 0, "Failed to read initial RTC calendar");
    zassert_equal(readback.tm_sec, initial.tm_sec, "Initial seconds differ");
    zassert_equal(readback.tm_min, initial.tm_min, "Initial minutes differ");
    zassert_equal(readback.tm_hour, initial.tm_hour, "Initial hours differ");
    zassert_equal(readback.tm_mday, initial.tm_mday, "Initial day differs");
    zassert_equal(readback.tm_mon, initial.tm_mon, "Initial month differs");
    zassert_equal(readback.tm_year, initial.tm_year, "Initial year differs");

    const time_t initial_epoch = timeutil_timegm(&initial);
    time_t previous_epoch = timeutil_timegm(&readback);
    bool reached_target = false;
    int elapsed_ms = 0;

    while (elapsed_ms < RTC_OBSERVATION_BOUND_SECONDS * 1000) {
        k_sleep(K_MSEC(RTC_POLL_INTERVAL_MS));
        elapsed_ms += RTC_POLL_INTERVAL_MS;

        struct rtc_time observed;
        zassert_equal(rtc_get_time(rtc, &observed), 0, "Failed to read RTC calendar");
        const time_t observed_epoch = timeutil_timegm(&observed);
        zassert_true(observed_epoch >= previous_epoch,
                     "RTC calendar moved backward (%lld < %lld)",
                     (long long)observed_epoch, (long long)previous_epoch);
        previous_epoch = observed_epoch;

        if (observed_epoch >= initial_epoch + 10) {
            reached_target = true;
            zassert_true(observed.tm_year > initial.tm_year ||
                             (observed.tm_year == initial.tm_year &&
                              (observed.tm_mon > initial.tm_mon ||
                               (observed.tm_mon == initial.tm_mon &&
                                observed.tm_mday >= initial.tm_mday))),
                         "RTC did not cross the year boundary");
            break;
        }
    }

    zassert_true(reached_target,
                 "RTC did not advance by ten calendar seconds within %d seconds",
                 RTC_OBSERVATION_BOUND_SECONDS);
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
