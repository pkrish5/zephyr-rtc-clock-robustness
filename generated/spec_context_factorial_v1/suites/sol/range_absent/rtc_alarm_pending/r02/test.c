#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_ID 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static bool at_or_after_alarm(const struct rtc_time *time)
{
    if (time->tm_year != 125) {
        return time->tm_year > 125;
    }
    if (time->tm_mon != 0) {
        return time->tm_mon > 0;
    }
    if (time->tm_mday != 1) {
        return time->tm_mday > 1;
    }
    return time->tm_hour > 0 || time->tm_min > 0 || time->tm_sec >= 5;
}

ZTEST(rtc_alarm_pending, test_new_year_alarm)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time readback;
    struct rtc_time now;
    uint16_t readback_mask;
    int pending;
    int64_t deadline;

    zassert_true(device_is_ready(rtc), "RTC is not ready");

    /* Discard a pending indication left by earlier board activity. */
    pending = rtc_alarm_is_pending(rtc, ALARM_ID);
    zassert_true(pending >= 0, "cannot read initial alarm state: %d", pending);

    zassert_ok(rtc_set_time(rtc, &start), "cannot set RTC calendar");
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm),
               "cannot set RTC alarm");
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &readback_mask, &readback),
               "cannot read RTC alarm");
    zassert_equal(readback_mask, ALARM_MASK, "alarm mask differs");
    zassert_equal(readback.tm_hour, 0, "alarm hour differs");
    zassert_equal(readback.tm_min, 0, "alarm minute differs");
    zassert_equal(readback.tm_sec, 5, "alarm second differs");

    zassert_ok(rtc_get_time(rtc, &now), "cannot read RTC calendar");
    zassert_false(at_or_after_alarm(&now),
                  "alarm time passed before observation began");

    /* The alarm is ten RTC seconds away; allow another ten for scheduling. */
    deadline = k_uptime_get() + 20000;
    do {
        zassert_ok(rtc_get_time(rtc, &now), "cannot read RTC calendar");
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0, "cannot read alarm state: %d", pending);
        if (pending != 0) {
            /* The alarm may have fired between the two reads. */
            zassert_ok(rtc_get_time(rtc, &now), "cannot reread RTC calendar");
            zassert_true(at_or_after_alarm(&now), "alarm pending before its time");
            return;
        }
        k_msleep(100);
    } while (k_uptime_get() < deadline);

    zassert_unreachable("alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
