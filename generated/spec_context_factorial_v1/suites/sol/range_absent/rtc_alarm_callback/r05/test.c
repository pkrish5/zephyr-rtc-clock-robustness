#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static atomic_t seen;
static atomic_t wrong_id;
static const uint16_t expected_id[] = { 0, 1 };

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    const uint16_t expected = *(const uint16_t *)user_data;

    (void)dev;
    if (id != expected) {
        atomic_set(&wrong_id, 1);
    } else {
        atomic_or(&seen, 1 << expected);
    }
}

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

static bool alarm_second(const struct rtc_time *t)
{
    return t->tm_year == 125 && t->tm_mon == 0 && t->tm_mday == 1 &&
           t->tm_hour == 0 && t->tm_min == 0 && t->tm_sec == 5;
}

ZTEST(rtc_alarm, test_both_channels_at_new_year)
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
    struct rtc_time now;
    int64_t deadline;

    zassert_true(device_is_ready(rtc));
    atomic_clear(&seen);
    atomic_clear(&wrong_id);
    zassert_ok(rtc_set_time(rtc, &start));

    for (uint16_t id = 0; id < 2; id++) {
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          (void *)&expected_id[id]));
    }

    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(before_alarm(&now), "alarm setup exceeded ten RTC seconds");
    zassert_equal(atomic_get(&seen), 0, "callback fired before alarm");

    /* Ten RTC seconds to the alarm, plus ten seconds for LSI and scheduling slack. */
    deadline = k_uptime_get() + 20000;
    while (k_uptime_get() < deadline) {
        atomic_val_t flags = atomic_get(&seen);

        zassert_ok(rtc_get_time(rtc, &now));
        zassert_equal(atomic_get(&wrong_id), 0, "wrong alarm ID");
        if (before_alarm(&now)) {
            zassert_equal(flags, 0, "callback fired before alarm time");
        } else if (flags == 3) {
            zassert_true(alarm_second(&now),
                         "callbacks were not observed at the alarm time");
            return;
        }
        k_sleep(K_MSEC(5));
    }

    zassert_equal(atomic_get(&seen), 3, "both alarm callbacks did not fire");
    zassert_unreachable("callbacks were not observed at the alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
