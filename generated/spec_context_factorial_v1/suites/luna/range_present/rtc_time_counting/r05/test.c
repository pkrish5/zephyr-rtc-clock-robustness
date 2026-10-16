#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVATION_BOUND K_SECONDS(30)
#define RTC_POLL_INTERVAL K_MSEC(100)

ZTEST(rtc_calendar, test_counts_across_year_boundary)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time initial = {
        .tm_sec = 50,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124,
    };
    struct rtc_time previous;
    struct rtc_time current;
    struct tm initial_tm = {0};
    struct tm current_tm = {0};
    int64_t initial_epoch;
    int64_t current_epoch;
    int ret;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");
    zassert_ok(rtc_set_time(rtc, &initial), "Setting initial RTC calendar failed");
    zassert_ok(rtc_get_time(rtc, &previous), "Reading initial RTC calendar failed");

    zassert_equal(previous.tm_sec, initial.tm_sec);
    zassert_equal(previous.tm_min, initial.tm_min);
    zassert_equal(previous.tm_hour, initial.tm_hour);
    zassert_equal(previous.tm_mday, initial.tm_mday);
    zassert_equal(previous.tm_mon, initial.tm_mon);
    zassert_equal(previous.tm_year, initial.tm_year);

    initial_tm.tm_sec = previous.tm_sec;
    initial_tm.tm_min = previous.tm_min;
    initial_tm.tm_hour = previous.tm_hour;
    initial_tm.tm_mday = previous.tm_mday;
    initial_tm.tm_mon = previous.tm_mon;
    initial_tm.tm_year = previous.tm_year;
    initial_epoch = timeutil_timegm(&initial_tm);

    for (int64_t waited_ms = 0;
         waited_ms <= k_ticks_to_ms_floor64(RTC_OBSERVATION_BOUND);
         waited_ms += k_ticks_to_ms_floor64(RTC_POLL_INTERVAL)) {
        k_sleep(RTC_POLL_INTERVAL);
        ret = rtc_get_time(rtc, &current);
        zassert_ok(ret, "Reading RTC calendar failed");

        current_tm.tm_sec = current.tm_sec;
        current_tm.tm_min = current.tm_min;
        current_tm.tm_hour = current.tm_hour;
        current_tm.tm_mday = current.tm_mday;
        current_tm.tm_mon = current.tm_mon;
        current_tm.tm_year = current.tm_year;
        current_epoch = timeutil_timegm(&current_tm);

        zassert_true(current_epoch >= timeutil_timegm(&(struct tm){
                         .tm_sec = previous.tm_sec,
                         .tm_min = previous.tm_min,
                         .tm_hour = previous.tm_hour,
                         .tm_mday = previous.tm_mday,
                         .tm_mon = previous.tm_mon,
                         .tm_year = previous.tm_year,
                     }),
                     "RTC calendar moved backward");

        if (current_epoch >= initial_epoch + 10) {
            zassert_true(current.tm_year > initial.tm_year ||
                         current.tm_mon > initial.tm_mon ||
                         current.tm_mday > initial.tm_mday,
                         "RTC did not cross the year boundary");
            return;
        }
        previous = current;
    }

    zassert_true(false,
                 "RTC did not advance by ten calendar seconds within 30 seconds");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
