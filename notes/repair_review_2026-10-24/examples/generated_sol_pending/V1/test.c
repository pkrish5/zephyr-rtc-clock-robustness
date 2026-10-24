#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/util.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static bool before_time(const struct rtc_time *a, const struct rtc_time *b)
{
    const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
                       a->tm_hour, a->tm_min, a->tm_sec };
    const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
                       b->tm_hour, b->tm_min, b->tm_sec };

    for (size_t i = 0; i < 6; i++) {
        if (av[i] != bv[i]) {
            return av[i] < bv[i];
        }
    }
    return false;
}

ZTEST(rtc_alarm_pending, test_alarm_pending_at_new_year)
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
    bool saw_before = false;
    bool saw_after = false;
    bool reached = false;
    int pending;
    int64_t deadline;

    zassert_true(device_is_ready(rtc));
    const int64_t repair_deadline = k_uptime_get() + 20824;
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm));
    zassert_ok(rtc_alarm_get_time(rtc, 0, &mask, &readback));
    zassert_equal(mask, ALARM_MASK);
    zassert_equal(readback.tm_hour, alarm.tm_hour);
    zassert_equal(readback.tm_min, alarm.tm_min);
    zassert_equal(readback.tm_sec, alarm.tm_sec);

    /* Share one 20,824-ms observation ceiling from the calendar reset. */
    deadline = repair_deadline;
    while (k_uptime_get() < deadline) {
        zassert_ok(rtc_get_time(rtc, &now));
        if (!before_time(&now, &alarm)) {
            reached = true;
            break;
        }

        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &now));
        if (before_time(&now, &alarm)) {
            zassert_equal(pending, 0, "alarm pending before its time");
            saw_before = true;
        } else {
            reached = true;
            saw_after = pending > 0;
            break;
        }
        k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
    }

    zassert_true(saw_before, "no pre-alarm observation");
    zassert_true(reached, "RTC did not reach alarm time");

    /* Preserve the service allowance, capped by the shared observation ceiling. */
    deadline = MIN(k_uptime_get() + 3000, repair_deadline);
    while (!saw_after && k_uptime_get() < deadline) {
        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);
        saw_after = pending > 0;
        if (!saw_after) {
            k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
        }
    }
    zassert_true(saw_after, "alarm never became pending");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
