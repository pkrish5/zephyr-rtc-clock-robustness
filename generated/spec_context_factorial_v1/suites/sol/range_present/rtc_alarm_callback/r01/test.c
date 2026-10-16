#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define RTC_NODE DT_ALIAS(rtc)
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc_dev = DEVICE_DT_GET(RTC_NODE);
static K_SEM_DEFINE(alarm_event, 0, 2);

struct alarm_observation {
    uint16_t expected_id;
    atomic_t count;
};

static struct alarm_observation alarms[2] = {
    { .expected_id = 0 },
    { .expected_id = 1 },
};
static atomic_t wrong_id;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    struct alarm_observation *obs = user_data;

    if (dev != rtc_dev || id != obs->expected_id) {
        atomic_set(&wrong_id, 1);
    }
    atomic_inc(&obs->count);
    k_sem_give(&alarm_event);
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

ZTEST(rtc_alarm, test_both_alarms_across_midnight)
{
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
    };
    const struct rtc_time target = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
        .tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
    };
    struct rtc_time now;
    bool reached_target = false;
    int64_t deadline;

    zassert_true(device_is_ready(rtc_dev), "RTC is not ready");
    atomic_set(&wrong_id, 0);
    for (int id = 0; id < 2; id++) {
        atomic_set(&alarms[id].count, 0);
    }
    k_sem_reset(&alarm_event);

    zassert_equal(rtc_set_time(rtc_dev, &start), 0, "set RTC time failed");
    for (int id = 0; id < 2; id++) {
        zassert_equal(rtc_alarm_set_time(rtc_dev, id, ALARM_MASK, &target), 0,
                      "set alarm %d failed", id);
        zassert_equal(rtc_alarm_set_callback(rtc_dev, id, alarm_callback,
                                             &alarms[id]), 0,
                      "set callback %d failed", id);
    }

    /* Ten RTC seconds take at most 10 * 32000 / 17000 = 18.83 s.
     * Thirty seconds also allows time for setup and callback delivery.
     */
    deadline = k_uptime_get() + 30000;
    while (k_uptime_get() < deadline) {
        int count0 = atomic_get(&alarms[0].count);
        int count1 = atomic_get(&alarms[1].count);

        zassert_equal(rtc_get_time(rtc_dev, &now), 0, "read RTC failed");
        if (before_alarm(&now)) {
            zassert_equal(count0, 0, "alarm 0 fired before target time");
            zassert_equal(count1, 0, "alarm 1 fired before target time");
        } else {
            reached_target = true;
            if (count0 != 0 && count1 != 0) {
                break;
            }
        }
        (void)k_sem_take(&alarm_event, K_MSEC(20));
    }

    zassert_true(reached_target, "RTC did not reach target time");
    zassert_equal(atomic_get(&wrong_id), 0, "callback reported wrong alarm ID");
    zassert_equal(atomic_get(&alarms[0].count), 1, "alarm 0 callback missing");
    zassert_equal(atomic_get(&alarms[1].count), 1, "alarm 1 callback missing");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
