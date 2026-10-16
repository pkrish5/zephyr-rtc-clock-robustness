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
#define DEADLINE_MS 30000

static const struct rtc_time start_time = {
    .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
    .tm_wday = 2, .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
};
static const struct rtc_time alarm_time = {
    .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
    .tm_wday = 3, .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
};

struct observation {
    uint16_t expected_id;
    atomic_t count;
    atomic_t error;
};

static struct observation observations[2];
static struct k_sem callback_sem;

static int compare_time(const struct rtc_time *a, const struct rtc_time *b)
{
    const int x[] = {a->tm_year, a->tm_mon, a->tm_mday,
                     a->tm_hour, a->tm_min, a->tm_sec};
    const int y[] = {b->tm_year, b->tm_mon, b->tm_mday,
                     b->tm_hour, b->tm_min, b->tm_sec};

    for (int i = 0; i < 6; ++i) {
        if (x[i] != y[i]) {
            return x[i] < y[i] ? -1 : 1;
        }
    }
    return 0;
}

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
    struct observation *observation = user_data;
    struct rtc_time observed_time;

    if (id != observation->expected_id ||
        rtc_get_time(dev, &observed_time) != 0 ||
        compare_time(&observed_time, &alarm_time) != 0) {
        atomic_set(&observation->error, 1);
    }
    atomic_inc(&observation->count);
    k_sem_give(&callback_sem);
}

ZTEST(rtc_alarm, both_channels_at_new_year)
{
    const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
    struct rtc_time now;
    int64_t deadline;

    zassert_true(device_is_ready(rtc));
    k_sem_init(&callback_sem, 0, 2);
    for (uint16_t id = 0; id < 2; ++id) {
        observations[id].expected_id = id;
        atomic_set(&observations[id].count, 0);
        atomic_set(&observations[id].error, 0);
    }

    zassert_ok(rtc_set_time(rtc, &start_time));
    /* Ten RTC seconds take at most 10 * 32000 / 17000 = 18.83 s.
     * The 30 s deadline adds over 11 s for setup and interrupt delivery;
     * oscillator limits alone do not bound that delivery latency.
     */
    deadline = k_uptime_get() + DEADLINE_MS;

    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time));
        zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
                                          &observations[id]));
    }

    /* Sample callback counts before reading the calendar, avoiding a false
     * premature result if an alarm arrives during the calendar read.
     */
    do {
        atomic_val_t count0 = atomic_get(&observations[0].count);
        atomic_val_t count1 = atomic_get(&observations[1].count);

        zassert_ok(rtc_get_time(rtc, &now));
        if (compare_time(&now, &alarm_time) >= 0) {
            break;
        }
        zassert_equal(count0, 0, "alarm 0 fired before its time");
        zassert_equal(count1, 0, "alarm 1 fired before its time");
        zassert_true(k_uptime_get() < deadline, "RTC did not reach alarm time");
        k_sleep(K_MSEC(20));
    } while (true);

    for (int i = 0; i < 2; ++i) {
        int64_t remaining = deadline - k_uptime_get();

        zassert_true(remaining > 0, "alarm callback deadline expired");
        zassert_ok(k_sem_take(&callback_sem, K_MSEC(remaining)),
                   "missing alarm callback");
    }

    for (int i = 0; i < 2; ++i) {
        zassert_equal(atomic_get(&observations[i].count), 1,
                      "wrong callback count for alarm %d", i);
        zassert_equal(atomic_get(&observations[i].error), 0,
                      "wrong alarm ID or callback RTC time for alarm %d", i);
    }
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
