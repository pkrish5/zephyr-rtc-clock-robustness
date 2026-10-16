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

/* Compare calendar fields, including the year rollover. */
static int calendar_compare(const struct rtc_time *a,
                            const struct rtc_time *b)
{
    const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
                       a->tm_hour, a->tm_min, a->tm_sec };
    const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
                       b->tm_hour, b->tm_min, b->tm_sec };

    for (unsigned int i = 0; i < sizeof(av) / sizeof(av[0]); ++i) {
        if (av[i] != bv[i]) {
            return av[i] < bv[i] ? -1 : 1;
        }
    }
    return 0;
}

ZTEST(rtc_alarm_pending, test_calendar_rollover)
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
    uint16_t supported = 0;
    uint16_t read_mask = 0;
    bool saw_before = false;
    bool saw_pending = false;
    int rc;

    zassert_true(device_is_ready(rtc), "RTC device is not ready");
    zassert_equal(ALARM_MASK, 7U, "Unexpected alarm mask");
    rc = rtc_alarm_get_supported_fields(rtc, ALARM_ID, &supported);
    zassert_equal(rc, 0, "Supported-fields query failed: %d", rc);
    zassert_equal(supported & ALARM_MASK, ALARM_MASK,
                  "Required alarm fields are unsupported");

    /* Disable both hardware channels and consume any stale pending state. */
    for (uint16_t id = 0; id < 2; ++id) {
        rc = rtc_alarm_set_time(rtc, id, 0, NULL);
        zassert_equal(rc, 0, "Disable alarm %u failed: %d", id, rc);
        rc = rtc_alarm_is_pending(rtc, id);
        zassert_true(rc == 0 || rc == 1,
                     "Pending query for alarm %u failed: %d", id, rc);
    }

    /* The target is ten RTC seconds away. Thirty uptime seconds allow
     * ample margin for RTC tick phase and scheduling, but bound failures
     * such as a stopped RTC. No wall-clock synchronization is needed.
     */
    int64_t deadline = k_uptime_get() + 30000;

    rc = rtc_set_time(rtc, &start);
    zassert_equal(rc, 0, "Set calendar failed: %d", rc);
    rc = rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &target);
    zassert_equal(rc, 0, "Set alarm failed: %d", rc);
    rc = rtc_alarm_get_time(rtc, ALARM_ID, &read_mask, &readback);
    zassert_equal(rc, 0, "Read alarm failed: %d", rc);
    zassert_equal(read_mask, ALARM_MASK, "Alarm mask mismatch");
    zassert_equal(readback.tm_sec, target.tm_sec, "Second mismatch");
    zassert_equal(readback.tm_min, target.tm_min, "Minute mismatch");
    zassert_equal(readback.tm_hour, target.tm_hour, "Hour mismatch");

    while (k_uptime_get() < deadline) {
        struct rtc_time now;
        int pending = rtc_alarm_is_pending(rtc, ALARM_ID);

        zassert_true(pending == 0 || pending == 1,
                     "Pending query failed: %d", pending);
        /* Read the calendar after querying pending so a legitimate alarm
         * arriving across the target tick is not reported as premature.
         * Each pending query may consume the pending indication.
         */
        rc = rtc_get_time(rtc, &now);
        zassert_equal(rc, 0, "Read calendar failed: %d", rc);
        if (calendar_compare(&now, &target) < 0) {
            zassert_equal(pending, 0, "Alarm pending before target calendar time");
            saw_before = true;
        } else if (pending == 1) {
            saw_pending = true;
            break;
        }
        k_sleep(K_MSEC(10));
    }

    rc = rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL);
    zassert_equal(rc, 0, "Alarm cleanup failed: %d", rc);
    zassert_true(saw_before, "No pre-target observation was made");
    zassert_true(saw_pending,
                 "No pending alarm at/after target within 30 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
