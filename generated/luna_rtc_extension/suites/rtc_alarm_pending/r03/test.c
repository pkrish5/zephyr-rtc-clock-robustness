#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time start = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
		.tm_wday = 2,
		.tm_yday = 365,
		.tm_isdst = -1,
	};
	struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
		.tm_mday = 1,
		.tm_mon = 0,
		.tm_year = 125,
		.tm_wday = 3,
		.tm_yday = 0,
		.tm_isdst = -1,
	};
	struct rtc_time readback;
	bool pending;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "rtc_set_time failed");
	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, ALARM_MASK,
				      &alarm), "rtc_alarm_set_time failed");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback),
		   "rtc_alarm_get_time failed");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	/* Allow the calendar to advance past the start time, still 9 s early. */
	k_sleep(K_SECONDS(1));
	zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
		   "rtc_alarm_is_pending failed before alarm time");
	zassert_false(pending, "Alarm became pending before its configured time");

	/* Poll at 100 ms intervals for 15 s: 10 s until alarm plus 5 s margin. */
	for (int i = 0; i < 150; ++i) {
		zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
			   "rtc_alarm_is_pending failed while waiting");
		if (pending) {
			break;
		}
		k_sleep(K_MSEC(100));
	}
	zassert_true(pending, "Alarm did not become pending within 15 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
