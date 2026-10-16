#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static const struct rtc_time alarm_time = {
    .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
    .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
};

static struct k_sem alarm_event;
static atomic_t fired[2];
static atomic_t wrong_id;
static uint16_t expected_ids[2] = { 0, 1 };

static bool before_alarm(const struct rtc_time *t)
{
    if (t->tm_year != alarm_time.tm_year) {
        return t->tm_year < alarm_time.tm_year;
    }
    if (t->tm_mon != alarm_time.tm_mon) {
        return t->tm_mon < alarm_time.tm_mon;
    }
    if (t->tm_mday != alarm_time.tm_mday) {
        return t->tm_mday < alarm_time.tm_mday;
    }
    if (t->tm_hour != alarm_time.tm_hour) {
        return t->tm_hour < alarm_time.tm_hour;
    }
    if (t->tm_min != alarm_time.tm_min) {
        return t->tm_min < alarm_time.tm_min;
    }
    return t->tm_sec < alarm_time.tm_sec;
}

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
    uint16_t expected = *(uint16_t *)user_data;

    ARG_UNUSED(dev);
    if (id != expected || id >= 2) {
        atomic_set(&wrong_id, 1);
    } else {
        atomic_inc(&fired[id]);
    }
    k_sem_give(&alarm_event);
}

ZTEST(rtc_alarm, test_both_channels_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365,
    };
    struct rtc_time observed;
    int64_t deadline;

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    k_sem_init(&alarm_event, 0, 2);
    atomic_clear(&fired[0]);
    atomic_clear(&fired[1]);
    atomic_clear(&wrong_id);

    zassert_ok(rtc_set_time(rtc, &start));
    for (uint16_t id = 0; id < 2; id++) {
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time));
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          &expected_ids[id]));
    }

    /* Ten RTC seconds take at most 18.83 wall seconds at 17 kHz.
     * The rest of this 60-second test budget allows ISR and thread delivery;
     * the oscillator specification alone does not bound that latency.
     */
    deadline = k_uptime_get() + 60000;
    while (k_uptime_get() < deadline) {
        zassert_ok(rtc_get_time(rtc, &observed));
        if (before_alarm(&observed) &&
            (atomic_get(&fired[0]) || atomic_get(&fired[1]))) {
            /* Confirm the calendar is still early across the callback read. */
            zassert_ok(rtc_get_time(rtc, &observed));
            zassert_false(before_alarm(&observed),
                          "alarm callback arrived before 00:00:05");
        }
        zassert_false(atomic_get(&wrong_id), "callback reported wrong alarm ID");
        if (atomic_get(&fired[0]) && atomic_get(&fired[1])) {
            break;
        }
        (void)k_sem_take(&alarm_event, K_MSEC(10));
    }

    zassert_ok(rtc_get_time(rtc, &observed));
    zassert_false(before_alarm(&observed), "RTC did not reach alarm time");
    zassert_false(atomic_get(&wrong_id), "callback reported wrong alarm ID");
    zassert_equal(atomic_get(&fired[0]), 1, "alarm 0 did not fire once");
    zassert_equal(atomic_get(&fired[1]), 1, "alarm 1 did not fire once");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
