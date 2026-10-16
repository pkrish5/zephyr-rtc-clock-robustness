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
	const struct rtc_time start = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
	};
	const struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
	};
	struct rtc_time readback;
	struct rtc_time now;
	bool pending;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "rtc_set_time failed");
	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
				      &alarm), "rtc_alarm_set_time failed");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback),
		   "rtc_alarm_get_time failed");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	zassert_ok(rtc_get_time(rtc, &now), "rtc_get_time failed");
	zassert_true(now.tm_year == 124 && now.tm_mon == 11 &&
		     now.tm_mday == 31 && now.tm_hour == 23 &&
		     now.tm_min == 59 && now.tm_sec < 5,
		     "calendar should still be before the alarm time");
	zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
		   "rtc_alarm_is_pending failed");
	zassert_false(pending, "alarm became pending before its configured time");

	/* At the slowest documented LSI rate, a calendar second can take about
	 * 1.89 s with the 128 x 250 prescaler. Allow 30 s for the ten-second
	 * calendar advance (including tick phase) and polling/thread scheduling.
	 */
	int64_t deadline = k_uptime_get() + 30000;
	do {
		zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
			   "rtc_alarm_is_pending failed");
		if (pending) {
			break;
		}
		k_sleep(K_MSEC(100));
	} while (k_uptime_get() < deadline);

	zassert_true(pending, "alarm did not become pending within 30 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
