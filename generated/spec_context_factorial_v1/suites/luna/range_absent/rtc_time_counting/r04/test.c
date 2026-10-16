#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVE_INTERVAL K_SECONDS(1)
#define RTC_OBSERVE_BOUND K_SECONDS(30)

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time initial = {
        .tm_sec = 50,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 126,
        .tm_wday = -1,
        .tm_yday = -1,
        .tm_isdst = -1,
    };
    struct rtc_time observed;
    struct rtc_time previous;
    int64_t initial_seconds;
    int64_t observed_seconds;
    int64_t previous_seconds;
    int ret;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");

    ret = rtc_set_time(rtc, &initial);
    zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);

    ret = rtc_get_time(rtc, &observed);
    zassert_equal(ret, 0, "initial rtc_get_time failed: %d", ret);
    zassert_equal(observed.tm_year, initial.tm_year, "initial year mismatch");
    zassert_equal(observed.tm_mon, initial.tm_mon, "initial month mismatch");
    zassert_equal(observed.tm_mday, initial.tm_mday, "initial day mismatch");
    zassert_equal(observed.tm_hour, initial.tm_hour, "initial hour mismatch");
    zassert_equal(observed.tm_min, initial.tm_min, "initial minute mismatch");
    zassert_equal(observed.tm_sec, initial.tm_sec, "initial second mismatch");

    initial_seconds = timeutil_timegm(&initial);
    previous = observed;
    previous_seconds = timeutil_timegm(&previous);
    zassert_true(previous_seconds >= initial_seconds,
                 "RTC read is before the set calendar time");

    for (int elapsed_ms = 0; elapsed_ms < 30000; elapsed_ms += 1000) {
        k_sleep(RTC_OBSERVE_INTERVAL);
        ret = rtc_get_time(rtc, &observed);
        zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);

        observed_seconds = timeutil_timegm(&observed);
        zassert_true(observed_seconds >= previous_seconds,
                     "RTC calendar moved backward");
        previous = observed;
        previous_seconds = observed_seconds;

        if (observed_seconds - initial_seconds >= 10) {
            break;
        }
    }

    zassert_true(previous_seconds - initial_seconds >= 10,
                 "RTC did not advance ten seconds within 30 seconds");
    zassert_true(previous.tm_year > initial.tm_year,
                 "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
