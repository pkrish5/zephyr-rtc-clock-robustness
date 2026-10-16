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
		.tm_mday = 1,
		.tm_mon = 0,
		.tm_year = 125,
	};
	struct rtc_time readback = {0};
	struct rtc_time now = {0};
	int err;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Could not set RTC calendar");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_CHANNEL, ALARM_MASK, &alarm),
		   "Could not set RTC alarm");
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_CHANNEL, &readback),
		   "Could not read RTC alarm");
	zassert_equal(readback.tm_sec, alarm.tm_sec, "Alarm seconds mismatch");
	zassert_equal(readback.tm_min, alarm.tm_min, "Alarm minutes mismatch");
	zassert_equal(readback.tm_hour, alarm.tm_hour, "Alarm hours mismatch");

	/* Verify the alarm remains clear while the calendar is still before it. */
	k_sleep(K_SECONDS(2));
	zassert_ok(rtc_get_time(rtc, &now), "Could not read RTC calendar");
	zassert_true(now.tm_year == 124 && now.tm_mon == 11 &&
		     now.tm_mday == 31 && now.tm_hour == 23 &&
		     now.tm_min == 59 && now.tm_sec < alarm.tm_sec,
		     "RTC should still be before the alarm");
	err = rtc_alarm_is_pending(rtc, ALARM_CHANNEL);
	zassert_equal(err, 0, "Alarm became pending before configured time");

	/* The alarm is five seconds away; allow ten seconds for RTC tick and
	 * driver observation latency after checking that it is not yet pending.
	 */
	for (int elapsed = 0; elapsed < 10; elapsed++) {
		err = rtc_alarm_is_pending(rtc, ALARM_CHANNEL);
		zassert_true(err >= 0, "Could not query RTC alarm pending state");
		if (err > 0) {
			return;
		}
		k_sleep(K_SECONDS(1));
	}

	zassert_ok(rtc_get_time(rtc, &now), "Could not read RTC calendar");
	zassert_true(now.tm_year > 124 || now.tm_mon > 11 || now.tm_mday > 31 ||
		     now.tm_hour > 23 || now.tm_min > 59 ||
		     (now.tm_hour == 0 && now.tm_min == 0 && now.tm_sec >= 5),
		     "RTC did not reach the configured alarm time");
	err = rtc_alarm_is_pending(rtc, ALARM_CHANNEL);
	zassert_equal(err, 1, "Alarm was not pending after reaching alarm time");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
