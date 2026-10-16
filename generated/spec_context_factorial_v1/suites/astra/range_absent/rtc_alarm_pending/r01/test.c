#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static int calendar_compare(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
			   a->tm_hour, a->tm_min, a->tm_sec };
	const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
			   b->tm_hour, b->tm_min, b->tm_sec };

	for (unsigned int i = 0; i < 6; ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

ZTEST(rtc_alarm_pending, test_new_year_alarm)
{
	const struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	};
	const struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	};
	const uint16_t mask = RTC_ALARM_TIME_MASK_SECOND |
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR;
	struct rtc_time readback;
	uint16_t supported = 0;
	uint16_t readback_mask = 0;
	bool checked_early = false;
	bool observed_pending = false;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(mask, 7, "Unexpected alarm field mask");

	/* Disable both channels and consume any previous pending state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		rc = rtc_alarm_is_pending(rtc, id);
		zassert_true(rc == 0 || rc == 1, "Pending query failed: %d", rc);
	}

	zassert_ok(rtc_alarm_get_supported_fields(rtc, 0, &supported));
	zassert_equal(supported & mask, mask, "Required fields unsupported");
	zassert_ok(rtc_set_time(rtc, &start));

	/* Ten RTC seconds to the target; allow 30 wall-clock seconds for
	 * oscillator tolerance, RTC synchronization and scheduling overhead.
	 * The independent uptime deadline also detects a stopped RTC.
	 */
	const int64_t deadline = k_uptime_get() + 30000;

	zassert_ok(rtc_alarm_set_time(rtc, 0, mask, &target));
	zassert_ok(rtc_alarm_get_time(rtc, 0, &readback_mask, &readback));
	zassert_equal(readback_mask, mask);
	zassert_equal(readback.tm_sec, target.tm_sec);
	zassert_equal(readback.tm_min, target.tm_min);
	zassert_equal(readback.tm_hour, target.tm_hour);

	while (k_uptime_get() < deadline) {
		struct rtc_time before, after;

		/* Bracket the destructive pending query with calendar reads so
		 * a tick during the query cannot cause a false early failure.
		 */
		zassert_ok(rtc_get_time(rtc, &before));
		rc = rtc_alarm_is_pending(rtc, 0);
		zassert_true(rc == 0 || rc == 1, "Pending query failed: %d", rc);
		zassert_ok(rtc_get_time(rtc, &after));
		zassert_true(calendar_compare(&after, &before) >= 0,
			     "RTC moved backwards");

		if (calendar_compare(&after, &target) < 0) {
			zassert_equal(rc, 0, "Alarm pending before target calendar time");
			checked_early = true;
		}
		if (rc == 1) {
			zassert_true(calendar_compare(&after, &target) >= 0,
				     "Alarm pending before target calendar time");
			observed_pending = true;
			break;
		}
		k_msleep(20);
	}

	zassert_ok(rtc_alarm_set_time(rtc, 0, 0, NULL));
	zassert_true(checked_early, "No pre-target observation was made");
	zassert_true(observed_pending, "Alarm did not become pending within 30 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
