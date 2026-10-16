#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define RTC_DEVICE DEVICE_DT_GET(DT_ALIAS(rtc))
#define ALARM_CHANNEL 0
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

ZTEST(rtc_alarm_pending, test_alarm_pending_across_new_year)
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
	struct rtc_time readback = {0};
	struct rtc_time now = {0};

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm),
		   "Failed to configure RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_CHANNEL, &readback),
		   "Failed to read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec);
	zassert_equal(readback.tm_min, alarm.tm_min);
	zassert_equal(readback.tm_hour, alarm.tm_hour);

	/* At most 10 RTC seconds to cross the target at the documented LSI
	 * and prescaler extremes, plus 2 seconds for scheduling and delivery.
	 */
	for (int i = 0; i < 12; i++) {
		zassert_ok(rtc_get_time(rtc, &now), "Failed to read RTC calendar");
		if (now.tm_year > 124 ||
		    (now.tm_year == 124 && now.tm_mon > 11) ||
		    (now.tm_year == 124 && now.tm_mon == 11 && now.tm_mday > 31) ||
		    (now.tm_year == 124 && now.tm_mon == 11 && now.tm_mday == 31 &&
		     (now.tm_hour > 23 ||
		      (now.tm_hour == 23 && now.tm_min > 59) ||
		      (now.tm_hour == 23 && now.tm_min == 59 && now.tm_sec >= 55)))) {
			break;
		}
		zassert_false(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
			      "Alarm became pending before configured time");
		k_sleep(K_MSEC(100));
	}

	/* The slowest supported oscillator gives about 7.2 s per RTC second
	 * with this prescaler. Allow 120 s total for calendar rollover and
	 * thread/ISR delivery latency; the oscillator specification alone
	 * cannot bound the latter.
	 */
	for (int i = 0; i < 1200; i++) {
		zassert_ok(rtc_get_time(rtc, &now), "Failed to read RTC calendar");
		if (now.tm_year > 125 ||
		    (now.tm_year == 125 && now.tm_mon > 0) ||
		    (now.tm_year == 125 && now.tm_mon == 0 && now.tm_mday > 1) ||
		    (now.tm_year == 125 && now.tm_mon == 0 && now.tm_mday == 1 &&
		     (now.tm_hour > 0 || now.tm_min > 0 || now.tm_sec >= 5))) {
			break;
		}
		k_sleep(K_MSEC(100));
	}
	zassert_true(now.tm_year > 125 ||
		     (now.tm_year == 125 && now.tm_mon > 0) ||
		     (now.tm_year == 125 && now.tm_mon == 0 && now.tm_mday > 1) ||
		     (now.tm_year == 125 && now.tm_mon == 0 && now.tm_mday == 1 &&
		      (now.tm_hour > 0 || now.tm_min > 0 || now.tm_sec >= 5)),
		     "RTC did not reach alarm time within 120 s");
	zassert_true(rtc_alarm_is_pending(rtc, ALARM_CHANNEL),
		     "Alarm did not become pending after configured time");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
