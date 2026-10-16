#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

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
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55, .tm_wday = 2,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5, .tm_wday = 3,
    };
    struct rtc_time now;
    struct rtc_time readback;
    uint16_t readback_mask;
    int pending;
    int64_t deadline;

    zassert_true(device_is_ready(rtc));
    zassert_true(rtc_alarm_is_pending(rtc, ALARM_ID) >= 0);
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &readback_mask, &readback));
    zassert_equal(readback_mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, 0);
    zassert_equal(readback.tm_min, 0);
    zassert_equal(readback.tm_sec, 5);

    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(before_alarm(&now));
    pending = rtc_alarm_is_pending(rtc, ALARM_ID);
    zassert_equal(pending, 0);
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(before_alarm(&now));

    /* Ten RTC seconds take at most 18.83 s at 17 kHz / (128 * 250).
     * Allow 30 s for calendar progress and scheduling.
     */
    deadline = k_uptime_get() + 30000;
    while (before_alarm(&now) && k_uptime_get() < deadline) {
        k_sleep(K_MSEC(20));
        zassert_ok(rtc_get_time(rtc, &now));
    }
    zassert_false(before_alarm(&now), "RTC did not reach alarm time");

    /* Give interrupt delivery and thread polling a separate finite 30 s
     * allowance; the oscillator specification does not bound that latency.
     */
    deadline = k_uptime_get() + 30000;
    do {
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0);
        if (pending == 1) {
            break;
        }
        k_sleep(K_MSEC(20));
    } while (k_uptime_get() < deadline);
    zassert_equal(pending, 1, "alarm never became pending");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
