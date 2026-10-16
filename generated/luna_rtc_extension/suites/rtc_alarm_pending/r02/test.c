#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending_at_time)
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
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_equal(rtc_set_time(rtc, &start), 0, "Could not set RTC calendar");
	zassert_equal(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
					 &alarm), 0, "Could not set RTC alarm");
	zassert_equal(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback), 0,
		      "Could not read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec, "Alarm seconds differ");
	zassert_equal(readback.tm_min, alarm.tm_min, "Alarm minutes differ");
	zassert_equal(readback.tm_hour, alarm.tm_hour, "Alarm hours differ");

	ret = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL);
	zassert_equal(ret, 0, "Alarm unexpectedly pending before configured time");

	/* The programmed time is ten seconds ahead; allow a further ten seconds
	 * for RTC tick/driver observation latency.
	 */
	for (int i = 0; i < 20; i++) {
		k_sleep(K_SECONDS(1));
		ret = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL);
		if (ret > 0) {
			break;
		}
		zassert_equal(ret, 0, "RTC alarm pending check failed");
	}
	zassert_true(ret > 0, "RTC alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
