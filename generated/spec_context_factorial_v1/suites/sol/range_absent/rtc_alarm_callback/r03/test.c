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

static const struct device *const rtc_dev = DEVICE_DT_GET(RTC_NODE);
static const uint16_t alarm_ids[] = { 0, 1 };
static atomic_t seen;
static atomic_t wrong_id;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    const uint16_t expected = *(const uint16_t *)user_data;

    if (dev != rtc_dev || id != expected) {
        atomic_set(&wrong_id, 1);
    } else {
        atomic_or(&seen, (atomic_val_t)(1U << expected));
    }
}

ZTEST(rtc_alarm, test_both_channels_at_new_year)
{
    struct rtc_time start = {
        .tm_year = 2024 - 1900,
        .tm_mon = 12 - 1,
        .tm_mday = 31,
        .tm_wday = 2,
        .tm_hour = 23,
        .tm_min = 59,
        .tm_sec = 55,
    };
    struct rtc_time alarm = {
        .tm_year = 2025 - 1900,
        .tm_mon = 1 - 1,
        .tm_mday = 1,
        .tm_wday = 3,
        .tm_hour = 0,
        .tm_min = 0,
        .tm_sec = 5,
    };
    struct rtc_time now;
    int64_t deadline;
    bool reached;

    zassert_true(device_is_ready(rtc_dev), "RTC is not ready");
    atomic_set(&seen, 0);
    atomic_set(&wrong_id, 0);

    zassert_ok(rtc_set_time(rtc_dev, &start));
    for (uint16_t id = 0; id < 2; id++) {
        zassert_ok(rtc_alarm_set_time(rtc_dev, id, ALARM_MASK, &alarm));
        zassert_ok(rtc_alarm_set_callback(rtc_dev, id, alarm_callback,
                                          (void *)&alarm_ids[id]));
    }

    /* Give both alarms a full ten RTC seconds after configuration. */
    zassert_ok(rtc_set_time(rtc_dev, &start));
    deadline = k_uptime_get() + 30000; /* Allows for LSI clock tolerance. */

    for (;;) {
        zassert_ok(rtc_get_time(rtc_dev, &now));
        reached = now.tm_year == 2025 - 1900 && now.tm_mon == 0 &&
                  now.tm_mday == 1 && now.tm_hour == 0 &&
                  now.tm_min == 0 && now.tm_sec >= 5;

        if (!reached) {
            zassert_equal(atomic_get(&seen), 0,
                          "an alarm fired before the RTC alarm time");
        } else if (atomic_get(&seen) == 0x3) {
            break;
        }

        zassert_equal(atomic_get(&wrong_id), 0,
                      "an alarm callback reported the wrong channel");
        zassert_true(k_uptime_get() < deadline,
                     "RTC alarms did not fire within 30 seconds");
        k_sleep(K_MSEC(25));
    }

    zassert_equal(atomic_get(&wrong_id), 0,
                  "an alarm callback reported the wrong channel");
    zassert_true(now.tm_sec <= 6,
                 "both callbacks must be observed at the alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
