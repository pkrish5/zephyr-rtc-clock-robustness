#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    zassert_true(device_is_ready(rtc), "RTC device is not ready");

    struct rtc_time initial = {
        .tm_sec = 50,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124,
        .tm_wday = 2,
        .tm_yday = 365,
        .tm_isdst = -1,
    };
    int ret = rtc_set_time(rtc, &initial);
    zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);

    struct rtc_time prev;
    ret = rtc_get_time(rtc, &prev);
    zassert_equal(ret, 0, "rtc_get_time after set failed: %d", ret);
    zassert_equal(prev.tm_year, initial.tm_year, "year mismatch");
    zassert_equal(prev.tm_mon, initial.tm_mon, "month mismatch");
    zassert_equal(prev.tm_mday, initial.tm_mday, "day mismatch");
    zassert_equal(prev.tm_hour, initial.tm_hour, "hour mismatch");
    zassert_equal(prev.tm_min, initial.tm_min, "minute mismatch");
    zassert_equal(prev.tm_sec, initial.tm_sec, "second mismatch");

    /* Allow 30 seconds: comfortably over ten LSI-clocked RTC seconds while
     * remaining a finite bound for scheduling and oscillator variation. */
    for (int i = 0; i < 30; i++) {
        k_sleep(K_MSEC(1000));

        struct rtc_time now;
        ret = rtc_get_time(rtc, &now);
        zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);

        /* Fields are compared lexicographically in RTC's calendar ordering. */
        bool backwards = now.tm_year < prev.tm_year ||
            (now.tm_year == prev.tm_year && now.tm_mon < prev.tm_mon) ||
            (now.tm_year == prev.tm_year && now.tm_mon == prev.tm_mon &&
             now.tm_mday < prev.tm_mday) ||
            (now.tm_year == prev.tm_year && now.tm_mon == prev.tm_mon &&
             now.tm_mday == prev.tm_mday && now.tm_hour < prev.tm_hour) ||
            (now.tm_year == prev.tm_year && now.tm_mon == prev.tm_mon &&
             now.tm_mday == prev.tm_mday && now.tm_hour == prev.tm_hour &&
             now.tm_min < prev.tm_min) ||
            (now.tm_year == prev.tm_year && now.tm_mon == prev.tm_mon &&
             now.tm_mday == prev.tm_mday && now.tm_hour == prev.tm_hour &&
             now.tm_min == prev.tm_min && now.tm_sec < prev.tm_sec);
        zassert_false(backwards, "RTC calendar moved backward");

        if (now.tm_year > initial.tm_year ||
            (now.tm_year == initial.tm_year &&
             (now.tm_mon > initial.tm_mon ||
              (now.tm_mon == initial.tm_mon &&
               (now.tm_mday > initial.tm_mday ||
                (now.tm_mday == initial.tm_mday &&
                 (now.tm_hour > initial.tm_hour ||
                  (now.tm_hour == initial.tm_hour &&
                   (now.tm_min > initial.tm_min ||
                    (now.tm_min == initial.tm_min &&
                     now.tm_sec >= initial.tm_sec + 10)))))))))) {
            zassert_true(now.tm_year > initial.tm_year,
                         "RTC did not cross the year boundary");
            return;
        }
        prev = now;
    }

    zassert_unreachable("RTC did not advance ten calendar seconds within 30 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
