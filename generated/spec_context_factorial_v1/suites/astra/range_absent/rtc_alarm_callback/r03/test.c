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

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
K_SEM_DEFINE(events, 0, 2);

struct observation {
    atomic_t calls;
    uint16_t reported_id;
    int read_result;
    struct rtc_time time;
};

static struct observation observations[2];

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
    struct observation *observation = user_data;

    /* Preserve the first event, including any premature invocation. */
    if (atomic_inc(&observation->calls) == 0) {
        observation->reported_id = id;
        /* STM32's RTC time read accesses registers without blocking. */
        observation->read_result = rtc_get_time(dev, &observation->time);
        k_sem_give(&events);
    }
}

static void check_event(unsigned int id)
{
    const struct observation *observation = &observations[id];
    const struct rtc_time *time = &observation->time;

    zassert_equal(atomic_get(&observations[id].calls), 1,
                  "Alarm %u callback count", id);
    zassert_equal(observation->reported_id, id,
                  "Alarm %u reported the wrong channel", id);
    zassert_ok(observation->read_result, "Callback RTC read failed");
    zassert_equal(time->tm_year, 125, "Wrong callback year");
    zassert_equal(time->tm_mon, 0, "Wrong callback month");
    zassert_equal(time->tm_mday, 1, "Wrong callback day");
    zassert_equal(time->tm_hour, 0, "Wrong callback hour");
    zassert_equal(time->tm_min, 0, "Wrong callback minute");
    zassert_equal(time->tm_sec, 5, "Premature or late callback");
}

ZTEST(rtc_alarm, test_both_channels_across_new_year)
{
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    struct rtc_time alarm = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
        .tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    int wait_result[2];
    int disable_result[2];
    int callback_result[2];

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");
    k_sem_reset(&events);

    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
        zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
        zassert_true(rtc_alarm_is_pending(rtc, id) >= 0,
                     "Cannot clear pending alarm");
        atomic_clear(&observations[id].calls);
    }

    zassert_ok(rtc_set_time(rtc, &start));

    /*
     * Ten RTC seconds can take substantially longer than ten kernel
     * seconds with the uncalibrated LSI. Thirty kernel seconds allows
     * more than a factor of two plus setup and scheduling margin.
     * Both events share this deadline.
     */
    int64_t deadline = k_uptime_get() + 30000;

    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                         &observations[id]));
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
    }

    for (unsigned int i = 0; i < 2; ++i) {
        int64_t remaining = deadline - k_uptime_get();

        wait_result[i] = k_sem_take(&events,
                                   remaining > 0 ? K_MSEC(remaining) :
                                                   K_NO_WAIT);
    }

    /* Quiesce callbacks before assertions, including on timeout. */
    for (uint16_t id = 0; id < 2; ++id) {
        disable_result[id] = rtc_alarm_set_time(rtc, id, 0, NULL);
        callback_result[id] = rtc_alarm_set_callback(rtc, id, NULL, NULL);
    }

    for (unsigned int id = 0; id < 2; ++id) {
        zassert_ok(disable_result[id]);
        zassert_ok(callback_result[id]);
        zassert_ok(wait_result[id], "Both alarms did not arrive within 30 s");
    }

    /*
     * Semaphore publication protects the captured records. Checking
     * each FIRST callback's complete calendar timestamp proves that
     * neither callback occurred early, including before midnight.
     */
    check_event(0);
    check_event(1);
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
