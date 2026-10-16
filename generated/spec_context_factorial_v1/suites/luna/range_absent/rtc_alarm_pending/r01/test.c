#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

ZTEST(rtc_alarm_pending, test_alarm_pending)
{
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
		.tm_mday = 1,
		.tm_mon = 0,
		.tm_year = 125,
	};
	struct rtc_time actual;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "rtc_set_time failed");
	zassert_ok(rtc_get_time(rtc, &actual), "rtc_get_time failed");
	zassert_equal(actual.tm_year, start.tm_year);
	zassert_equal(actual.tm_mon, start.tm_mon);
	zassert_equal(actual.tm_mday, start.tm_mday);
	zassert_equal(actual.tm_hour, start.tm_hour);
	zassert_equal(actual.tm_min, start.tm_min);
	zassert_equal(actual.tm_sec, start.tm_sec);

	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
				      &alarm),
		   "rtc_alarm_set_time failed");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &actual),
		   "rtc_alarm_get_time failed");
	zassert_equal(actual.tm_sec, alarm.tm_sec);
	zassert_equal(actual.tm_min, alarm.tm_min);
	zassert_equal(actual.tm_hour, alarm.tm_hour);

	k_sleep(K_SECONDS(2));
	zassert_false(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL),
		      "alarm became pending before configured time");

	/* Start is 10 seconds before alarm; allow 15 seconds for RTC tick and
	 * alarm propagation, which exceeds the expected calendar interval.
	 */
	for (int elapsed = 0; elapsed < 15; elapsed++) {
		if (rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL)) {
			return;
		}
		k_sleep(K_SECONDS(1));
	}
	zassert_true(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL),
		     "alarm did not become pending within 15 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
