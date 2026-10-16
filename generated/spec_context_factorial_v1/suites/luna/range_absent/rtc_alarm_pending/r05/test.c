#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
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
	struct rtc_time actual;
	uint16_t actual_mask;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm),
		   "Failed to configure RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_CHANNEL, &actual_mask, &actual),
		   "Failed to read RTC alarm");
	zassert_equal(actual_mask, ALARM_MASK, "Alarm mask mismatch");
	zassert_equal(actual.tm_sec, alarm.tm_sec, "Alarm seconds mismatch");
	zassert_equal(actual.tm_min, alarm.tm_min, "Alarm minutes mismatch");
	zassert_equal(actual.tm_hour, alarm.tm_hour, "Alarm hours mismatch");

	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC calendar");
	zassert_false(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		      "Alarm pending immediately after setting calendar");

	/* Wait at most 20 s: the target is 10 s ahead, with ample scheduling margin. */
	int64_t deadline = k_uptime_get() + 20000;
	while (k_uptime_get() < deadline) {
		if (rtc_alarm_is_pending(rtc, ALARM_CHANNEL)) {
			return;
		}
		k_sleep(K_MSEC(100));
	}
	zassert_true(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		     "RTC alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
