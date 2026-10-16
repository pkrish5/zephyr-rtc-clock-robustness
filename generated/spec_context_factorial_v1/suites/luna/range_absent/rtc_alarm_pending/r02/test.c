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
	};
	struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
	};
	struct rtc_time readback;
	bool pending;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "failed to set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm),
		   "failed to configure RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_CHANNEL, &readback),
		   "failed to read back RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	/* This is well before the 10-second interval to the alarm. */
	k_sleep(K_SECONDS(1));
	zassert_ok(rtc_alarm_is_pending(rtc, ALARM_CHANNEL, &pending),
		   "failed to check RTC alarm pending state");
	zassert_false(pending, "alarm became pending before its configured time");

	/* The alarm is 10 seconds after the set time. Allow 15 seconds total
	 * for RTC tick phase and scheduling latency.
	 */
	for (int i = 0; i < 14; ++i) {
		zassert_ok(rtc_alarm_is_pending(rtc, ALARM_CHANNEL, &pending),
			   "failed to check RTC alarm pending state");
		if (pending) {
			break;
		}
		k_sleep(K_SECONDS(1));
	}
	zassert_true(pending, "alarm did not become pending within 15 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
