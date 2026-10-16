#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_ID 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static bool at_or_after_alarm(const struct rtc_time *t)
{
    if (t->tm_year != 125) return t->tm_year > 125;
    if (t->tm_mon != 0) return t->tm_mon > 0;
    if (t->tm_mday != 1) return t->tm_mday > 1;
    if (t->tm_hour != 0) return t->tm_hour > 0;
    if (t->tm_min != 0) return t->tm_min > 0;
    return t->tm_sec >= 5;
}

ZTEST(rtc_alarm, test_pending_across_new_year)
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
        .tm_wday = 3, .tm_yday = 0,
    };
    struct rtc_time readback;
    uint16_t mask = 0;
    int64_t deadline;
    bool saw_before = false;
    bool saw_pending = false;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_true(rtc_alarm_is_pending(rtc, ALARM_ID) >= 0);
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
    zassert_equal(mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, 0);
    zassert_equal(readback.tm_min, 0);
    zassert_equal(readback.tm_sec, 5);

    /* Ten RTC seconds take at most 10 * 32000 / 17000 = 18.83 s.
     * The 30 s deadline also allows time for polling and interrupt delivery;
     * it is a test limit, since the oscillator bound gives no ISR latency bound.
     */
    deadline = k_uptime_get() + 30000;
    while (k_uptime_get() < deadline && !saw_pending) {
        struct rtc_time before, after;
        int pending;

        zassert_ok(rtc_get_time(rtc, &before));
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &after));

        if (!at_or_after_alarm(&before) && !at_or_after_alarm(&after)) {
            saw_before = true;
            zassert_equal(pending, 0,
                          "alarm pending before its calendar time");
        }
        if (pending > 0 && at_or_after_alarm(&after)) {
            saw_pending = true;
        }
        if (!saw_pending) {
            k_sleep(K_MSEC(20));
        }
    }

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(saw_pending, "alarm did not become pending within 30 s");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
