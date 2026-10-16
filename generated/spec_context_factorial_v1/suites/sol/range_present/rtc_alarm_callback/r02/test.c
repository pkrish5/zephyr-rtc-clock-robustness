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

struct alarm_event {
    atomic_t count;
    atomic_t id;
    atomic_t read_result;
    struct rtc_time when;
};

static struct alarm_event events[2];
K_SEM_DEFINE(alarm_sem, 0, 2);

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    struct alarm_event *event = user_data;

    atomic_set(&event->id, id);
    atomic_set(&event->read_result, rtc_get_time(dev, &event->when));
    atomic_inc(&event->count);
    k_sem_give(&alarm_sem);
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

ZTEST(rtc_alarm, test_both_alarm_channels)
{
    const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time now;
    int64_t deadline;

    zassert_true(device_is_ready(rtc));
    zassert_ok(rtc_set_time(rtc, &start));

    for (int i = 0; i < 2; ++i) {
        atomic_set(&events[i].count, 0);
        zassert_ok(rtc_alarm_set_time(rtc, i, ALARM_MASK, &alarm));
        zassert_ok(rtc_alarm_set_callback(rtc, i, alarm_callback, &events[i]));
    }

    /* Ten RTC seconds take at most 10 * 32000 / 17000 < 19 real
     * seconds at the specified LSI minimum. The 45-second test bound
     * leaves additional time for interrupt and thread delivery; that
     * delivery margin is a test allowance, not a hardware guarantee.
     */
    deadline = k_uptime_get() + 45000;
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(before_alarm(&now), "alarms were armed too late");

    while (true) {
        int count0 = atomic_get(&events[0].count);
        int count1 = atomic_get(&events[1].count);

        zassert_ok(rtc_get_time(rtc, &now));
        if (!before_alarm(&now)) {
            break;
        }
        zassert_equal(count0, 0, "alarm 0 fired early");
        zassert_equal(count1, 0, "alarm 1 fired early");
        zassert_true(k_uptime_get() < deadline, "RTC did not reach alarm time");
        k_sleep(K_MSEC(10));
    }

    while (atomic_get(&events[0].count) == 0 ||
           atomic_get(&events[1].count) == 0) {
        int64_t remaining = deadline - k_uptime_get();

        zassert_true(remaining > 0, "alarm callback timed out");
        (void)k_sem_take(&alarm_sem, K_MSEC(remaining));
    }

    for (int i = 0; i < 2; ++i) {
        const struct rtc_time *t = &events[i].when;

        zassert_equal(atomic_get(&events[i].count), 1);
        zassert_equal(atomic_get(&events[i].id), i);
        zassert_equal(atomic_get(&events[i].read_result), 0);
        zassert_equal(t->tm_year, 125);
        zassert_equal(t->tm_mon, 0);
        zassert_equal(t->tm_mday, 1);
        zassert_equal(t->tm_hour, 0);
        zassert_equal(t->tm_min, 0);
        zassert_equal(t->tm_sec, 5);
    }
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
