#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

static bool before(const struct rtc_time *a, const struct rtc_time *b)
{
    if (a->tm_year != b->tm_year) return a->tm_year < b->tm_year;
    if (a->tm_mon != b->tm_mon) return a->tm_mon < b->tm_mon;
    if (a->tm_mday != b->tm_mday) return a->tm_mday < b->tm_mday;
    if (a->tm_hour != b->tm_hour) return a->tm_hour < b->tm_hour;
    if (a->tm_min != b->tm_min) return a->tm_min < b->tm_min;
    return a->tm_sec < b->tm_sec;
}

ZTEST(rtc_alarm, pending_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    const uint16_t alarm_mask = RTC_ALARM_TIME_MASK_SECOND |
                                RTC_ALARM_TIME_MASK_MINUTE |
                                RTC_ALARM_TIME_MASK_HOUR;
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365
    };
    const struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5
    };
    struct rtc_time readback;
    struct rtc_time now;
    uint16_t readback_mask;
    bool saw_before = false;
    bool saw_pending = false;
    int pending;

    zassert_true(device_is_ready(rtc));
    pending = rtc_alarm_is_pending(rtc, 0); /* Consume any stale pending state. */
    zassert_true(pending >= 0);

    zassert_ok(rtc_set_time(rtc, &start));
    /* At 17 kHz, ten calendar seconds take at most 18.83 real seconds.
     * The 30-second test limit also allows over 11 seconds for execution
     * and interrupt delivery; it is a test margin, not an ISR guarantee.
     */
    int64_t deadline = k_uptime_get() + 30000;

    zassert_ok(rtc_alarm_set_time(rtc, 0, alarm_mask, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, 0, &readback_mask, &readback));
    zassert_equal(readback_mask, alarm_mask);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    while (k_uptime_get() < deadline) {
        /* Sample pending first, then calendar time: a pending sample is
         * considered early only if the later calendar sample is still early.
         */
        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &now));

        if (before(&now, &alarm)) {
            saw_before = true;
            zassert_equal(pending, 0, "alarm pending before its time");
        } else if (pending == 1) {
            saw_pending = true;
            break;
        }
        k_msleep(10);
    }

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(saw_pending, "alarm did not become pending within 30 seconds");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
