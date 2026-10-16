#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_IDS ((1U << 0) | (1U << 1))

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static K_SEM_DEFINE(alarm_events, 0, 2);
static atomic_t alarm_ids_seen;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    ARG_UNUSED(dev);
    ARG_UNUSED(user_data);

    if (id < 2U) {
        atomic_or(&alarm_ids_seen, (atomic_val_t)(1U << id));
    }
    k_sem_give(&alarm_events);
}

ZTEST(rtc_alarm_callback, test_both_alarm_channels)
{
    struct rtc_time start = {
        .tm_sec = 55,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124,
    };
    struct rtc_time alarm = {
        .tm_sec = 5,
        .tm_min = 0,
        .tm_hour = 0,
        .tm_mday = 1,
        .tm_mon = 0,
        .tm_year = 125,
    };
    struct rtc_time now;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");
    atomic_clear(&alarm_ids_seen);
    k_sem_reset(&alarm_events);

    zassert_ok(rtc_set_time(rtc, &start), "Could not set RTC time");
    zassert_ok(rtc_alarm_set_callback(rtc, 0, alarm_callback, NULL),
               "Could not register alarm 0 callback");
    zassert_ok(rtc_alarm_set_callback(rtc, 1, alarm_callback, NULL),
               "Could not register alarm 1 callback");
    zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm),
               "Could not set alarm 0");
    zassert_ok(rtc_alarm_set_time(rtc, 1, ALARM_MASK, &alarm),
               "Could not set alarm 1");

    /* Leave eight seconds before the alarm; callbacks must still be absent. */
    k_sleep(K_SECONDS(2));
    zassert_equal(atomic_get(&alarm_ids_seen), 0, "Callback fired prematurely");
    zassert_equal(k_sem_count_get(&alarm_events), 0, "Alarm event arrived prematurely");

    /* Allow 12 seconds for the remaining eight-second interval plus scheduling margin. */
    zassert_ok(rtc_get_time(rtc, &now), "Could not read RTC time");
    for (int i = 0; i < 2; i++) {
        zassert_ok(k_sem_take(&alarm_events, K_SECONDS(12)),
                   "Timed out waiting for an RTC alarm callback");
    }

    zassert_equal(atomic_get(&alarm_ids_seen), ALARM_IDS,
                  "Callbacks did not report both configured alarm IDs");
    zassert_true(now.tm_year > alarm.tm_year ||
                 (now.tm_year == alarm.tm_year &&
                  (now.tm_mon > alarm.tm_mon ||
                   (now.tm_mon == alarm.tm_mon &&
                    (now.tm_mday > alarm.tm_mday ||
                     (now.tm_mday == alarm.tm_mday &&
                      (now.tm_hour > alarm.tm_hour ||
                       (now.tm_hour == alarm.tm_hour &&
                        (now.tm_min > alarm.tm_min ||
                         (now.tm_min == alarm.tm_min && now.tm_sec >= alarm.tm_sec))))))))),
                 "RTC had not reached the configured alarm time");
}

ZTEST_SUITE(rtc_alarm_callback, NULL, NULL, NULL, NULL, NULL);
