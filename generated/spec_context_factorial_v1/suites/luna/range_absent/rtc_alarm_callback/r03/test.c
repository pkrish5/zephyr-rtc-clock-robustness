#include <zephyr/atomic.h>
#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_A 0U
#define ALARM_B 1U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem alarm_sem;
static atomic_t callback_ids;

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
    ARG_UNUSED(dev);
    ARG_UNUSED(user_data);

    if (id == ALARM_A || id == ALARM_B) {
        atomic_or(&callback_ids, BIT(id));
    }
    k_sem_give(&alarm_sem);
}

ZTEST(rtc_alarm, test_both_alarms_at_configured_time)
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
    k_sem_init(&alarm_sem, 0, 2);
    atomic_clear(&callback_ids);

    zassert_ok(rtc_alarm_set_callback(rtc, ALARM_A, alarm_callback, NULL));
    zassert_ok(rtc_alarm_set_callback(rtc, ALARM_B, alarm_callback, NULL));
    zassert_ok(rtc_set_time(rtc, &start));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_A, &alarm, ALARM_MASK));
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_B, &alarm, ALARM_MASK));

    /* Eight seconds after 23:59:55 is still before the 00:00:05 alarm. */
    k_sleep(K_SECONDS(8));
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(now.tm_mon == 11 && now.tm_mday == 31 &&
                 now.tm_hour == 23 && now.tm_min == 59 && now.tm_sec < 5,
                 "RTC reached or passed the alarm time before the early check");
    zassert_equal(k_sem_count_get(&alarm_sem), 0,
                  "An alarm callback fired before the configured time");

    /* Allow up to five seconds for the next one-second RTC alarm tick. */
    zassert_ok(k_sem_take(&alarm_sem, K_SECONDS(5)),
               "First RTC alarm callback timed out");
    zassert_ok(k_sem_take(&alarm_sem, K_SECONDS(1)),
               "Second RTC alarm callback timed out");
    zassert_equal(atomic_get(&callback_ids), BIT(ALARM_A) | BIT(ALARM_B),
                  "Callbacks did not report both configured alarm IDs");
    zassert_ok(rtc_get_time(rtc, &now));
    zassert_true(now.tm_year == 125 && now.tm_mon == 0 && now.tm_mday == 1 &&
                 now.tm_hour == 0 && now.tm_min == 0 && now.tm_sec >= 5,
                 "Callbacks arrived before the configured RTC alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);