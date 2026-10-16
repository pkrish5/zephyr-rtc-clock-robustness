#include <stdint.h>
#include <stdbool.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_ID 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static uint64_t calendar_key(const struct rtc_time *t)
{
    return (((((uint64_t)t->tm_year * 12 + t->tm_mon) * 32 + t->tm_mday)
             * 24 + t->tm_hour) * 60 + t->tm_min) * 60 + t->tm_sec;
}

ZTEST(rtc_alarm, test_pending_across_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
    };
    const struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time readback;
    struct rtc_time now;
    uint16_t mask = 0;
    bool observed_before = false;
    bool observed_after = false;
    int64_t deadline;
    int pending;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));

    /* Discard any pending state left by an earlier alarm configuration. */
    pending = rtc_alarm_is_pending(rtc, ALARM_ID);
    zassert_true(pending >= 0);

    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
    zassert_equal(mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    /* The programmed transition is 10 seconds away; allow 20 seconds
     * for RTC tick alignment and scheduling delay.
     */
    deadline = k_uptime_get() + 20000;
    while (k_uptime_get() < deadline) {
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &now));

        if (calendar_key(&now) < calendar_key(&alarm)) {
            observed_before = true;
            zassert_equal(pending, 0, "alarm pending before its RTC time");
        } else if (pending) {
            observed_after = true;
            break;
        }

        k_sleep(K_MSEC(20));
    }

    zassert_true(observed_before, "did not observe the RTC before the alarm");
    zassert_true(observed_after, "alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
