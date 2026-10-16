#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time calendar = {
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
	};
	struct rtc_time readback = { 0 };
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &calendar), "Could not set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
				      &alarm),
		   "Could not configure RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback),
		   "Could not read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec, "Alarm second mismatch");
	zassert_equal(readback.tm_min, alarm.tm_min, "Alarm minute mismatch");
	zassert_equal(readback.tm_hour, alarm.tm_hour, "Alarm hour mismatch");

	/* One second of wall time is less than the ten RTC seconds to the alarm,
	 * even at the documented maximum LSI frequency (47 kHz).
	 */
	k_sleep(K_SECONDS(1));
	zassert_equal(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL), 0,
		      "Alarm became pending before its configured time");

	/* Ten RTC seconds take at most 18.83 wall seconds at the documented
	 * minimum LSI frequency (17 kHz) with the 128 x 250 prescaler. Allow
	 * five additional seconds for polling and delivery overhead.
	 */
	deadline = k_uptime_get() + 24000;
	while (k_uptime_get() < deadline) {
		int pending = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL);

		zassert_true(pending >= 0, "Could not query RTC alarm pending state");
		if (pending > 0) {
			return;
		}
		k_sleep(K_MSEC(100));
	}

	zassert_true(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL) > 0,
		     "RTC alarm did not become pending within the observation bound");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
