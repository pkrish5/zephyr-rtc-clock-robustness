#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

/* The slowest characterized LSI yields 17,000 / (128 * 250) = 0.53125
 * RTC ticks/s. Allow 20 s for the target second plus oscillator tolerance.
 * This is a calendar-time bound, not a bound on interrupt delivery latency.
 */
#define ALARM_OBSERVATION_BOUND K_SECONDS(20)

ZTEST(rtc_alarm_pending, test_alarm_pending)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time now = {
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
	struct rtc_time readback = {0};

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &now), "Setting RTC calendar failed");
	zassert_ok(rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, ALARM_MASK,
				      &alarm), "Setting RTC alarm failed");
	zassert_ok(rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &readback),
		   "Reading RTC alarm failed");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	k_sleep(K_SECONDS(2));
	zassert_ok(rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &readback.tm_sec),
		   "Checking RTC alarm pending state failed");
	zassert_false(readback.tm_sec, "Alarm became pending before its time");

	int64_t deadline = k_uptime_get() + ALARM_OBSERVATION_BOUND.ms;
	bool pending = false;

	while (k_uptime_get() < deadline) {
		int ret = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending);

		zassert_ok(ret, "Checking RTC alarm pending state failed");
		if (pending) {
			break;
		}
		k_sleep(K_MSEC(100));
	}
	zassert_true(pending, "RTC alarm did not become pending within bound");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
