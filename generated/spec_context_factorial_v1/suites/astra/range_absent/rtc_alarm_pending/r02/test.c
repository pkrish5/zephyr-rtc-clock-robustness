#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define ALARM_ID 0U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static int calendar_compare(const struct rtc_time *a, const struct rtc_time *b)
{
    const int av[] = {a->tm_year, a->tm_mon, a->tm_mday,
                      a->tm_hour, a->tm_min, a->tm_sec};
    const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday,
                      b->tm_hour, b->tm_min, b->tm_sec};

    for (unsigned int i = 0; i < sizeof(av) / sizeof(av[0]); ++i) {
        if (av[i] != bv[i]) {
            return av[i] < bv[i] ? -1 : 1;
        }
    }
    return 0;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
    const struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    const struct rtc_time target = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
        .tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    struct rtc_time readback = {0};
    struct rtc_time now;
    uint16_t mask = 0;
    bool observed_before = false;
    bool observed_pending = false;
    int pending;

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    zassert_equal(ALARM_MASK, 7U, "Unexpected alarm mask");

    /* Disable both hardware channels and consume any stale pending state. */
    for (uint16_t id = 0; id < 2U; ++id) {
        zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
                   "Cannot disable alarm %u", (unsigned int)id);
        pending = rtc_alarm_is_pending(rtc, id);
        zassert_true(pending == 0 || pending == 1,
                     "Cannot read alarm %u: %d", (unsigned int)id, pending);
    }

    /* The target is ten calendar seconds away. Twenty seconds allows
     * another ten seconds for tick phase, setup, and scheduling latency,
     * while still failing finitely if the RTC or alarm stops progressing.
     */
    const int64_t deadline = k_uptime_get() + 20000;

    zassert_ok(rtc_set_time(rtc, &start), "Cannot set calendar");
    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &target),
               "Cannot configure alarm");
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback),
               "Cannot read alarm configuration");
    zassert_equal(mask, ALARM_MASK, "Alarm mask mismatch");
    zassert_equal(readback.tm_sec, target.tm_sec, "Second mismatch");
    zassert_equal(readback.tm_min, target.tm_min, "Minute mismatch");
    zassert_equal(readback.tm_hour, target.tm_hour, "Hour mismatch");

    while (k_uptime_get() < deadline) {
        /* Pending reads consume the indication. Read the calendar afterward
         * so a legitimate alarm at a second boundary is not called early.
         */
        pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_true(pending == 0 || pending == 1,
                     "Pending query failed: %d", pending);
        zassert_ok(rtc_get_time(rtc, &now), "Cannot read calendar");

        if (calendar_compare(&now, &target) < 0) {
            zassert_equal(pending, 0, "Alarm became pending before target");
            observed_before = true;
        } else if (pending == 1) {
            observed_pending = true;
            break;
        }

        k_sleep(K_MSEC(20));
    }

    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL),
               "Cannot disable tested alarm");
    zassert_true(observed_before, "No pre-target observation was made");
    zassert_true(observed_pending,
                 "Alarm was not pending at/after target within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
