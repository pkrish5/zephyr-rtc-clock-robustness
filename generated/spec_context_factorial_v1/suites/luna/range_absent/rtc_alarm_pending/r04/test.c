#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
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
	};
	struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
	};
	struct rtc_time readback = {0};
	struct rtc_time now = {0};
	bool pending = false;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
				      &alarm), "Failed to set RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback),
		   "Failed to read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	/* The alarm is ten seconds in the future; it must not be pending yet. */
	zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
		   "Failed to check RTC alarm pending state");
	zassert_false(pending, "Alarm was pending before its configured time");

	/* Allow up to 15 seconds for RTC tick and alarm interrupt processing. */
	for (int i = 0; i < 150; i++) {
		zassert_ok(rtc_get_time(rtc, &now), "Failed to read RTC calendar");
		zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending),
			   "Failed to check RTC alarm pending state");
		if (pending) {
			break;
		}
		k_sleep(K_MSEC(100));
	}

	zassert_true(pending, "RTC alarm did not become pending within 15 seconds");
	zassert_true(now.tm_year > 124 ||
		     (now.tm_year == 124 &&
		      (now.tm_mon > 11 ||
		       (now.tm_mon == 11 &&
			(now.tm_mday > 31 ||
			 (now.tm_mday == 31 &&
			  (now.tm_hour > 23 ||
			   (now.tm_hour == 23 &&
			    (now.tm_min > 59 ||
			     (now.tm_min == 59 && now.tm_sec >= 5)))))))))),
		   "Alarm became pending before its configured calendar time");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
