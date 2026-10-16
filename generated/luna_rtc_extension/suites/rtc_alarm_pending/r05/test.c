#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_CHANNEL 0
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

ZTEST(rtc_alarm_pending, test_alarm_pending_at_configured_time)
{
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
	struct rtc_time actual;
	int pending;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC calendar");

	ret = rtc_alarm_set_time(rtc, RTC_ALARM_CHANNEL, RTC_ALARM_MASK,
				 &alarm);
	zassert_ok(ret, "Failed to configure RTC alarm");

	ret = rtc_alarm_get_time(rtc, RTC_ALARM_CHANNEL, &actual);
	zassert_ok(ret, "Failed to read RTC alarm");
	zassert_equal(actual.tm_sec, alarm.tm_sec);
	zassert_equal(actual.tm_min, alarm.tm_min);
	zassert_equal(actual.tm_hour, alarm.tm_hour);

	/* Let the RTC advance past 23:59:55, but remain well before midnight. */
	k_sleep(K_SECONDS(2));
	ret = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending);
	zassert_ok(ret, "Failed to check RTC alarm pending state");
	zassert_equal(pending, 0, "Alarm became pending before its configured time");

	/* The alarm is ten seconds ahead; allow 20 seconds for RTC tick and polling. */
	for (int i = 0; i < 20; i++) {
		ret = rtc_alarm_is_pending(rtc, RTC_ALARM_CHANNEL, &pending);
		zassert_ok(ret, "Failed to check RTC alarm pending state");
		if (pending != 0) {
			break;
		}
		k_sleep(K_SECONDS(1));
	}
	zassert_equal(pending, 1, "Alarm did not become pending within 20 seconds");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
