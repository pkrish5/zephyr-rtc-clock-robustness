#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

struct alarm_record {
    atomic_t count;
    atomic_t id;
    atomic_t read_result;
    struct rtc_time time;
};

static struct alarm_record records[2];

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    struct alarm_record *record = user_data;
    struct rtc_time time;
    int result = rtc_get_time(dev, &time);

    if (result == 0) {
        record->time = time;
    }
    atomic_set(&record->read_result, result);
    atomic_set(&record->id, id);
    atomic_inc(&record->count);
}

ZTEST(rtc_alarm, both_alarms_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
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

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    zassert_ok(rtc_set_time(rtc, &start), "could not set RTC time");

    for (uint16_t id = 0; id < 2; ++id) {
        atomic_set(&records[id].count, 0);
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
                   "could not set alarm %u", id);
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          &records[id]),
                   "could not register callback %u", id);
    }

    /* Ten RTC seconds remain. Twenty wall-clock seconds allow for LSI drift. */
    deadline = k_uptime_get() + 20000;
    for (;;) {
        int count0 = atomic_get(&records[0].count);
        int count1 = atomic_get(&records[1].count);

        zassert_ok(rtc_get_time(rtc, &now), "could not read RTC time");
        if (now.tm_year == 124 ||
            (now.tm_year == 125 && now.tm_mon == 0 &&
             now.tm_mday == 1 && now.tm_hour == 0 &&
             now.tm_min == 0 && now.tm_sec < 5)) {
            zassert_equal(count0, 0, "alarm 0 fired early");
            zassert_equal(count1, 0, "alarm 1 fired early");
        }

        if (atomic_get(&records[0].count) != 0 &&
            atomic_get(&records[1].count) != 0) {
            break;
        }
        zassert_true(k_uptime_get() < deadline, "alarm callback timed out");
        k_sleep(K_MSEC(20));
    }

    for (uint16_t id = 0; id < 2; ++id) {
        const struct rtc_time *time = &records[id].time;

        zassert_equal(atomic_get(&records[id].count), 1,
                      "alarm %u callback count", id);
        zassert_equal(atomic_get(&records[id].id), id,
                      "alarm %u reported wrong ID", id);
        zassert_equal(atomic_get(&records[id].read_result), 0,
                      "alarm %u callback could not read RTC", id);
        zassert_equal(time->tm_year, 125, "alarm %u year", id);
        zassert_equal(time->tm_mon, 0, "alarm %u month", id);
        zassert_equal(time->tm_mday, 1, "alarm %u day", id);
        zassert_equal(time->tm_hour, 0, "alarm %u hour", id);
        zassert_equal(time->tm_min, 0, "alarm %u minute", id);
        zassert_equal(time->tm_sec, 5, "alarm %u second", id);
    }
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
