#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

/* From 23:59:55 to 00:00:05 is 10 seconds; allow 5 seconds for
 * oscillator tolerance and scheduling while retaining a finite bound.
 */
#define ALARM_WAIT_MS 15000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callbacks;
static atomic_t unexpected_ids;

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
    ARG_UNUSED(dev);
    ARG_UNUSED(user_data);

    if (id > 1U) {
        atomic_set(&unexpected_ids, 1);
        return;
    }
    atomic_or(&callbacks, (atomic_val_t)1 << id);
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
    struct rtc_time now = {
        .tm_sec = 55,
        .tm_min = 59,
        .tm_hour = 23,
        .tm_mday = 31,
        .tm_mon = 11,
        .tm_year = 124,
        .tm_wday = 2,
    };
    const struct rtc_time alarm = {
        .tm_sec = 5,
        .tm_min = 0,
        .tm_hour = 0,
        .tm_mday = 1,
        .tm_mon = 0,
        .tm_year = 125,
        .tm_wday = 3,
    };

    zassert_true(device_is_ready(rtc), "RTC device is not ready");
    atomic_set(&callbacks, 0);
    atomic_set(&unexpected_ids, 0);

    zassert_ok(rtc_set_time(rtc, &now), "rtc_set_time failed");
    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback, NULL),
                   "setting callback for alarm %u failed", id);
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
                   "setting alarm %u failed", id);
    }

    k_sleep(K_SECONDS(2));
    zassert_equal(atomic_get(&callbacks), 0,
                  "alarm callback observed before configured alarm time");
    zassert_equal(atomic_get(&unexpected_ids), 0, "unexpected alarm ID");

    /* Poll pending state as a public observable and wait for both callbacks. */
    int64_t deadline = k_uptime_get() + ALARM_WAIT_MS;
    while (k_uptime_get() < deadline && atomic_get(&callbacks) != 0x3) {
        for (uint16_t id = 0; id < 2; ++id) {
            bool pending = false;
            int ret = rtc_alarm_is_pending(rtc, id, &pending);
            zassert_ok(ret, "checking alarm %u pending state failed", id);
            if (pending) {
                /* Pending may precede callback delivery; allow it to dispatch. */
                k_yield();
            }
        }
        k_sleep(K_MSEC(50));
    }

    zassert_equal(atomic_get(&callbacks), 0x3,
                  "both configured alarm channels did not fire in time");
    zassert_equal(atomic_get(&unexpected_ids), 0, "unexpected alarm ID");

    zassert_ok(rtc_get_time(rtc, &now), "rtc_get_time failed");
    zassert_equal(now.tm_year, 125, "RTC year at callback");
    zassert_equal(now.tm_mon, 0, "RTC month at callback");
    zassert_equal(now.tm_mday, 1, "RTC day at callback");
    zassert_equal(now.tm_hour, 0, "RTC hour at callback");
    zassert_equal(now.tm_min, 0, "RTC minute at callback");
    zassert_true(now.tm_sec >= 5 && now.tm_sec <= 20,
                 "RTC time outside alarm observation bound: %d", now.tm_sec);
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
