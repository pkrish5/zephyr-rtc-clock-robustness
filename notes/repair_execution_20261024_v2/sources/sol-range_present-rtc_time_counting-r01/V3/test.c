#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

static uint64_t calendar_key(const struct rtc_time *t)
{
    zassert_true(t->tm_year >= 100 && t->tm_year <= 199);
    zassert_true(t->tm_mon >= 0 && t->tm_mon <= 11);
    zassert_true(t->tm_mday >= 1 && t->tm_mday <= 31);
    zassert_true(t->tm_hour >= 0 && t->tm_hour <= 23);
    zassert_true(t->tm_min >= 0 && t->tm_min <= 59);
    zassert_true(t->tm_sec >= 0 && t->tm_sec <= 59);

    uint64_t key = (uint64_t)t->tm_year;

    key = key * 13 + (uint64_t)t->tm_mon;
    key = key * 32 + (uint64_t)t->tm_mday;
    key = key * 24 + (uint64_t)t->tm_hour;
    key = key * 60 + (uint64_t)t->tm_min;
    return key * 60 + (uint64_t)t->tm_sec;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    const struct rtc_time initial = {
        .tm_year = 123, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 0,
    };
    const struct rtc_time ten_seconds_later = {
        .tm_year = 124, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
    };
    struct rtc_time observed;
    uint64_t previous = calendar_key(&initial);
    const uint64_t target = calendar_key(&ten_seconds_later);
    int64_t started_ms;

    zassert_true(device_is_ready(rtc));
    zassert_equal(rtc_set_time(rtc, &initial), 0);
    zassert_equal(rtc_get_time(rtc, &observed), 0);
    previous = calendar_key(&observed);
    zassert_true(previous >= calendar_key(&initial));

    started_ms = k_uptime_get();
    while (previous < target && !repair_expired()) {
        uint64_t current;

        k_sleep(K_MSEC(100));
        zassert_equal(rtc_get_time(rtc, &observed), 0);
        current = calendar_key(&observed);
        zassert_true(current >= previous, "RTC calendar moved backward");
        previous = current;
    }

    /* At 17 kHz with a 32000-cycle prescaler, ten RTC seconds take
     * under 18.83 wall-clock seconds. Allow 40 seconds for observation.
     * The oscillator specification does not bound thread wake-up latency.
     */
    zassert_true(previous >= target, "RTC did not cross the year boundary within the observation budget");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
