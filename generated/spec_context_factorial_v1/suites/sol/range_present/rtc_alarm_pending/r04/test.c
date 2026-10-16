#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_NODE DT_ALIAS(rtc)
#define ALARM_ID 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static bool before_alarm(const struct rtc_time *t)
{
    if (t->tm_year != 125) {
        return t->tm_year < 125;
    }
    if (t->tm_mon != 0) {
        return t->tm_mon < 0;
    }
    if (t->tm_mday != 1) {
        return t->tm_mday < 1;
    }
    if (t->tm_hour != 0) {
        return t->tm_hour < 0;
    }
    if (t->tm_min != 0) {
        return t->tm_min < 0;
    }
    return t->tm_sec < 5;
}

ZTEST(rtc_alarm_pending, test_midnight_alarm)
{
    const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_wday = 2, .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
    };
    const struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_wday = 3, .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time readback;
    struct rtc_time before;
    struct rtc_time after;
    uint16_t read_mask;
    bool saw_before = false;
    bool saw_pending = false;
    int64_t deadline;
    int pending;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &read_mask, &readback));
    zassert_equal(read_mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    /* Ten RTC seconds take at most 10 * 32000 / 17000 = 18.83 s.
     * The 40 s observation window leaves over 21 s for software delivery;
     * the oscillator specification alone gives no ISR latency guarantee.
     */
    deadline = k_uptime_get() + 40000;
    do {
        zassert_ok(rtc_get_time(rtc, &before));
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &after));

        if (before_alarm(&after)) {
            saw_before = true;
            zassert_equal(pending, 0,
                          "alarm pending before configured RTC time");
        } else if (pending == 1) {
            saw_pending = true;
            break;
        }

        k_sleep(K_MSEC(20));
    } while (k_uptime_get() < deadline);

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(saw_pending, "alarm did not become pending within 40 s");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
