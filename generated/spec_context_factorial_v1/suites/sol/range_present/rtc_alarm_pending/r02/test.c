#include <stdbool.h>
#include <stdint.h>
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
    if (t->tm_year != 125) {
        return t->tm_year > 125;
    }
    if (t->tm_mon != 0) {
        return t->tm_mon > 0;
    }
    if (t->tm_mday != 1) {
        return t->tm_mday > 1;
    }
    return t->tm_hour > 0 || t->tm_min > 0 || t->tm_sec >= 5;
}

ZTEST(rtc_alarm, test_midnight_pending)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time readback = {0};
    struct rtc_time now = {0};
    uint16_t readback_mask = 0;
    int pending;

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &readback_mask, &readback));
    zassert_equal(readback_mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    pending = rtc_alarm_is_pending(rtc, ALARM_ID);
    zassert_true(pending >= 0, "Cannot read alarm pending state");
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(!at_or_after_alarm(&now), "Alarm time passed during setup");
    zassert_equal(pending, 0, "Alarm pending before configured RTC time");

    /* Ten RTC seconds take at most 18.83 wall seconds at 17 kHz with
     * the fixed 128 * 250 prescaler. Allow the rest of this 60-second
     * observation window for scheduling and interrupt delivery; the
     * oscillator specification alone does not bound that latency.
     */
    int64_t deadline = k_uptime_get() + 60000;

    do {
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0, "Cannot read alarm pending state");
        if (pending != 0) {
            zassert_ok(rtc_get_time(rtc, &now));
            zassert_true(at_or_after_alarm(&now),
                         "Alarm pending before configured RTC time");
            return;
        }
        k_sleep(K_MSEC(20));
    } while (k_uptime_get() < deadline);

    zassert_true(false, "Alarm did not become pending within 60 seconds");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
