#include <stdint.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_NODE DT_ALIAS(rtc)
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static atomic_t callback_count[2];
static atomic_t wrong_id_count;
static const uint16_t alarm_ids[2] = { 0, 1 };

static void alarm_callback(const struct device *dev, uint16_t alarm_id,
                           void *user_data)
{
    const uint16_t expected_id = *(const uint16_t *)user_data;

    (void)dev;
    if (alarm_id != expected_id) {
        atomic_inc(&wrong_id_count);
    } else {
        atomic_inc(&callback_count[expected_id]);
    }
}

static bool before_alarm(const struct rtc_time *t)
{
    if (t->tm_year != 125) return t->tm_year < 125;
    if (t->tm_mon != 0) return t->tm_mon < 0;
    if (t->tm_mday != 1) return t->tm_mday < 1;
    if (t->tm_hour != 0) return t->tm_hour < 0;
    if (t->tm_min != 0) return t->tm_min < 0;
    return t->tm_sec < 5;
}

ZTEST(rtc_alarms, test_both_channels_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
    };
    const struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time now;
    int64_t deadline;

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    atomic_clear(&callback_count[0]);
    atomic_clear(&callback_count[1]);
    atomic_clear(&wrong_id_count);

    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
                   "could not set alarm %u", id);
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          (void *)&alarm_ids[id]),
                   "could not set callback %u", id);
    }
    zassert_ok(rtc_set_time(rtc, &start), "could not set RTC time");

    /* Ten RTC seconds to the alarm; allow 30 real seconds for LSI error and scheduling. */
    deadline = k_uptime_get() + 30000;
    do {
        int count0 = atomic_get(&callback_count[0]);
        int count1 = atomic_get(&callback_count[1]);

        zassert_ok(rtc_get_time(rtc, &now), "could not read RTC time");
        zassert_equal(atomic_get(&wrong_id_count), 0, "callback reported wrong ID");
        if (before_alarm(&now)) {
            zassert_equal(count0, 0, "alarm 0 fired early");
            zassert_equal(count1, 0, "alarm 1 fired early");
        } else if (count0 > 0 && count1 > 0) {
            break;
        }
        k_sleep(K_MSEC(10));
    } while (k_uptime_get() < deadline);

    zassert_equal(atomic_get(&callback_count[0]), 1, "alarm 0 did not fire once");
    zassert_equal(atomic_get(&callback_count[1]), 1, "alarm 1 did not fire once");
    zassert_equal(atomic_get(&wrong_id_count), 0, "callback reported wrong ID");
    zassert_equal(now.tm_year, 125, "wrong alarm year");
    zassert_equal(now.tm_mon, 0, "wrong alarm month");
    zassert_equal(now.tm_mday, 1, "wrong alarm day");
    zassert_equal(now.tm_hour, 0, "wrong alarm hour");
    zassert_equal(now.tm_min, 0, "wrong alarm minute");
    zassert_true(now.tm_sec >= 5 && now.tm_sec <= 6,
                 "callbacks were not observed at the alarm time");
}

ZTEST_SUITE(rtc_alarms, NULL, NULL, NULL, NULL, NULL);
