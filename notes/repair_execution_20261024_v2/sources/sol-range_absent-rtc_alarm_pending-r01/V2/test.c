#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

#define ALARM_ID 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static bool before_alarm(const struct rtc_time *t)
{
    if (t->tm_year != 125) return t->tm_year < 125;
    if (t->tm_mon != 0) return t->tm_mon < 0;
    if (t->tm_mday != 1) return t->tm_mday < 1;
    if (t->tm_hour != 0) return t->tm_hour < 0;
    if (t->tm_min != 0) return t->tm_min < 0;
    return t->tm_sec < 5;
}

ZTEST(rtc_alarm_pending, test_new_year_alarm)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time readback;
    uint16_t mask;
    bool saw_before = false;
    bool saw_pending = false;
    int rc;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
    zassert_equal(mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, 0);
    zassert_equal(readback.tm_min, 0);
    zassert_equal(readback.tm_sec, 5);

    /* Clear any old pending state, then restore the full observation window. */
    rc = rtc_alarm_is_pending(rtc, ALARM_ID);
    zassert_true(rc >= 0);
    zassert_ok(rtc_set_time(rtc, &start));

    int64_t deadline = repair_deadline;

    do {
        struct rtc_time first;
        struct rtc_time second;

        zassert_ok(rtc_get_time(rtc, &first));
        rc = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(rc >= 0);
        zassert_ok(rtc_get_time(rtc, &second));

        if (before_alarm(&first) && before_alarm(&second)) {
            saw_before = true;
            zassert_equal(rc, 0, "alarm pending before 2025-01-01 00:00:05");
        }
        if (rc == 1 && !before_alarm(&second)) {
            saw_pending = true;
            break;
        }
        k_sleep(K_MSEC(50));
    } while (k_uptime_get() < deadline);

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(saw_pending, "alarm not pending within 16 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
