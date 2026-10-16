#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

static bool before_target(const struct rtc_time *t)
{
    if (t->tm_year != 125) return t->tm_year < 125;
    if (t->tm_mon != 0) return t->tm_mon < 0;
    if (t->tm_mday != 1) return t->tm_mday < 1;
    if (t->tm_hour != 0) return t->tm_hour < 0;
    if (t->tm_min != 0) return t->tm_min < 0;
    return t->tm_sec < 5;
}

ZTEST(rtc_alarm_pending, test_midnight_alarm)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    const uint16_t mask = RTC_ALARM_TIME_MASK_SECOND |
                          RTC_ALARM_TIME_MASK_MINUTE |
                          RTC_ALARM_TIME_MASK_HOUR;
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
        .tm_wday = 3,
    };
    struct rtc_time readback = {0};
    uint16_t read_mask = 0;
    bool saw_before = false;
    bool saw_pending = false;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, 0, mask, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, 0, &read_mask, &readback));
    zassert_equal(read_mask, mask);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    /* The alarm is ten RTC seconds away; allow ten more for scheduling. */
    int64_t deadline = k_uptime_get() + 20000;

    while (k_uptime_get() < deadline) {
        struct rtc_time now;
        int pending;

        zassert_ok(rtc_get_time(rtc, &now));
        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);

        if (pending != 0) {
            zassert_ok(rtc_get_time(rtc, &now));
            zassert_false(before_target(&now), "alarm pending before its RTC time");
            saw_pending = true;
            break;
        }
        if (before_target(&now)) {
            saw_before = true;
        }
        k_sleep(K_MSEC(50));
    }

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(saw_pending, "alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
