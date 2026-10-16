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
#define OBSERVATION_MS 20000

static int calendar_compare(const struct rtc_time *a,
                            const struct rtc_time *b)
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

ZTEST(rtc_alarm_pending, test_midnight_alarm)
{
    const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
    struct rtc_time start = {
        .tm_year = 124, .tm_mon = 11, .tm_mday = 31,
        .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
        .tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    struct rtc_time target = {
        .tm_year = 125, .tm_mon = 0, .tm_mday = 1,
        .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
        .tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
        .tm_nsec = 0,
    };
    struct rtc_time readback = {0};
    uint16_t supported = 0;
    uint16_t mask = 0;
    bool observed_before = false;
    bool observed_pending = false;
    bool reached_target = false;

    zassert_true(device_is_ready(rtc), "RTC is not ready");
    zassert_equal(ALARM_MASK, 7U, "Unexpected alarm mask");

    /* Isolate the test from both hardware alarm channels and stale events. */
    for (uint16_t id = 0; id < 2; ++id) {
        zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
                   "Cannot disable alarm %u", (unsigned int)id);
        int pending = rtc_alarm_is_pending(rtc, id);

        zassert_true(pending == 0 || pending == 1,
                     "Cannot drain alarm %u: %d", (unsigned int)id, pending);
    }

    zassert_ok(rtc_alarm_get_supported_fields(rtc, ALARM_ID, &supported),
               "Cannot query supported fields");
    zassert_equal(supported & ALARM_MASK, ALARM_MASK,
                  "Hour/minute/second alarm fields are unsupported");
    zassert_ok(rtc_set_time(rtc, &start), "Cannot set calendar");

    /* The target is ten RTC seconds away. Twenty monotonic seconds allow
     * a full extra ten seconds for tick phase, polling and scheduling.
     * A stopped or excessively slow RTC therefore fails finitely.
     */
    const int64_t deadline = k_uptime_get() + OBSERVATION_MS;

    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &target),
               "Cannot configure alarm");
    zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback),
               "Cannot read alarm");
    zassert_equal(mask, ALARM_MASK, "Alarm mask mismatch");
    zassert_equal(readback.tm_sec, target.tm_sec, "Second mismatch");
    zassert_equal(readback.tm_min, target.tm_min, "Minute mismatch");
    zassert_equal(readback.tm_hour, target.tm_hour, "Hour mismatch");

    while (k_uptime_get() < deadline) {
        struct rtc_time before = {0};
        struct rtc_time after = {0};

        zassert_ok(rtc_get_time(rtc, &before), "Calendar read failed");
        int pending = rtc_alarm_is_pending(rtc, ALARM_ID);
        zassert_ok(rtc_get_time(rtc, &after), "Calendar read failed");
        zassert_true(pending == 0 || pending == 1,
                     "Pending query failed: %d", pending);
        zassert_true(calendar_compare(&after, &before) >= 0,
                     "Calendar moved backwards");

        /* Bracket the pending query: a query crossing the target second
         * must not be mistaken for an early alarm. Pending reads may
         * consume the event, so retain the first positive observation.
         */
        if (calendar_compare(&after, &target) < 0) {
            observed_before = true;
            zassert_equal(pending, 0, "Alarm pending before target calendar time");
        } else {
            reached_target = true;
        }

        if (pending == 1) {
            observed_pending = true;
            break;
        }
        k_msleep(10);
    }

    zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL),
               "Cannot disable test alarm");
    zassert_true(observed_before, "No observation before target time");
    zassert_true(reached_target, "RTC did not reach target within 20 seconds");
    zassert_true(observed_pending, "Alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
