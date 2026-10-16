#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_DEVICE DEVICE_DT_GET(DT_ALIAS(rtc))
#define ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending_at_configured_time)
{
	const struct device *rtc = RTC_DEVICE;
	struct rtc_time start = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
		.tm_wday = 2,
		.tm_yday = 365,
	};
	struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
	};
	struct rtc_time got;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");

	ret = rtc_set_time(rtc, &start);
	zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);

	ret = rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm);
	zassert_equal(ret, 0, "rtc_alarm_set_time failed: %d", ret);

	ret = rtc_alarm_get_time(rtc, ALARM_CHANNEL, &got);
	zassert_equal(ret, 0, "rtc_alarm_get_time failed: %d", ret);
	zassert_equal(got.tm_sec, alarm.tm_sec, "alarm seconds mismatch");
	zassert_equal(got.tm_min, alarm.tm_min, "alarm minutes mismatch");
	zassert_equal(got.tm_hour, alarm.tm_hour, "alarm hours mismatch");

	ret = rtc_get_time(rtc, &got);
	zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);
	zassert_false(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		      "alarm was pending before its configured time");

	/* The target is ten seconds ahead; allow up to 20 seconds for RTC and
	 * test scheduling latency while keeping the wait finite.
	 */
	for (int i = 0; i < 20; ++i) {
		if (rtc_alarm_is_pending(rtc, ALARM_CHANNEL)) {
			return;
		}
		k_sleep(K_SECONDS(1));
	}

	zassert_true(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		     "alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
