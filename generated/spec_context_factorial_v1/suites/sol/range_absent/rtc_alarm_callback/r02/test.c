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

K_SEM_DEFINE(alarm_events, 0, 2);

static atomic_t fired[2];
static atomic_t wrong_id;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    uint16_t expected = *(const uint16_t *)user_data;

    ARG_UNUSED(dev);
    if (id == expected) {
        atomic_inc(&fired[expected]);
    } else {
        atomic_inc(&wrong_id);
    }
    k_sem_give(&alarm_events);
}

static bool before_alarm(const struct rtc_time *t)
{
    if (t->tm_year < 125) {
        return true;
    }
    return t->tm_year == 125 && t->tm_mon == 0 && t->tm_mday == 1 &&
           t->tm_hour == 0 && t->tm_min == 0 && t->tm_sec < 5;
}

ZTEST(rtc_alarms, both_channels_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
    static const uint16_t ids[2] = { 0, 1 };
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
    bool reached = false;

    zassert_true(device_is_ready(rtc));
    atomic_clear(&fired[0]);
    atomic_clear(&fired[1]);
    atomic_clear(&wrong_id);

    zassert_ok(rtc_set_time(rtc, &start));
    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          (void *)&ids[id]));
    }

    /* Ten RTC seconds are expected; twenty wall-clock seconds allow LSI drift. */
    deadline = k_uptime_get() + 20000;
    while (k_uptime_get() < deadline) {
        int count0 = atomic_get(&fired[0]);
        int count1 = atomic_get(&fired[1]);
        int bad = atomic_get(&wrong_id);

        zassert_ok(rtc_get_time(rtc, &now));
        if (before_alarm(&now)) {
            zassert_equal(count0, 0, "alarm 0 fired early");
            zassert_equal(count1, 0, "alarm 1 fired early");
            zassert_equal(bad, 0, "unexpected alarm ID");
        } else {
            reached = true;
            break;
        }
        k_sleep(K_MSEC(10));
    }
    zassert_true(reached, "RTC did not reach the alarm time");

    /* Allow one second for interrupt delivery and test-thread scheduling. */
    deadline = k_uptime_get() + 1000;
    while ((atomic_get(&fired[0]) == 0 || atomic_get(&fired[1]) == 0) &&
           k_uptime_get() < deadline) {
        (void)k_sem_take(&alarm_events, K_MSEC(10));
    }

    zassert_equal(atomic_get(&wrong_id), 0, "callback reported wrong ID");
    zassert_true(atomic_get(&fired[0]) > 0, "alarm 0 callback missing");
    zassert_true(atomic_get(&fired[1]) > 0, "alarm 1 callback missing");
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(now.tm_year == 125 && now.tm_mon == 0 &&
                 now.tm_mday == 1 && now.tm_hour == 0 &&
                 now.tm_min == 0 && now.tm_sec >= 5 && now.tm_sec <= 6,
                 "callbacks were not observed at the alarm time");
}

ZTEST_SUITE(rtc_alarms, NULL, NULL, NULL, NULL, NULL);
