#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/ztest.h>

#define ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

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
	struct rtc_time readback;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm),
		   "Failed to configure RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_CHANNEL, &readback),
		   "Failed to read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);
	zassert_false(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		      "Alarm pending before configured time");

	/* At 128 x 250, the characterized 17 kHz minimum LSI gives at least
	 * 4.15 seconds per RTC second. Allow 60 seconds for crossing the target
	 * calendar time, then 5 seconds for delivery to this thread. The latter
	 * is a finite observation allowance, not a hardware latency guarantee.
	 */
	for (int i = 0; i < 65; i++) {
		if (rtc_alarm_is_pending(rtc, ALARM_CHANNEL)) {
			return;
		}
		k_sleep(K_SECONDS(1));
	}

	zassert_true(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		     "Alarm did not become pending within observation bound");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
