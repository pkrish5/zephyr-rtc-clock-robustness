#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    zassert_true(device_is_ready(rtc), "RTC device is not ready");

    /* 2024-12-31 23:59:55 UTC: ten RTC seconds cross into the next year. */
    struct rtc_time initial = {
        .tm_sec = 55,
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

    struct rtc_time previous;
    ret = rtc_get_time(rtc, &previous);
    zassert_equal(ret, 0, "initial rtc_get_time failed: %d", ret);

    const time_t initial_seconds = timeutil_timegm(&initial);
    const time_t first_seconds = timeutil_timegm(&previous);
    zassert_equal(first_seconds, initial_seconds,
                  "initial RTC readback differs from the set calendar");

    /*
     * Poll calendar time for at most 30 seconds. This allows scheduler and
     * LSI/RTC quantization delays while remaining a finite bound; the target
     * is only ten RTC seconds after the initial calendar value.
     */
    bool reached_target = false;
    for (int elapsed_ms = 0; elapsed_ms < 30000; elapsed_ms += 100) {
        k_sleep(K_MSEC(100));

        struct rtc_time current;
        ret = rtc_get_time(rtc, &current);
        zassert_equal(ret, 0, "rtc_get_time failed while polling: %d", ret);

        const time_t current_seconds = timeutil_timegm(&current);
        zassert_true(current_seconds >= first_seconds,
                     "RTC calendar moved backward");
        zassert_true(current_seconds >= initial_seconds,
                     "RTC calendar moved before initial value");

        if (current_seconds >= initial_seconds + 10) {
            zassert_true(current.tm_year > initial.tm_year,
                         "RTC did not cross the year boundary");
            reached_target = true;
            break;
        }
        previous = current;
    }

    zassert_true(reached_target,
                 "RTC did not advance ten calendar seconds within 30 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
