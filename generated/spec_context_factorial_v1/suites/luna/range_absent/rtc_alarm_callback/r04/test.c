#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_DEVICE DEVICE_DT_GET(DT_ALIAS(rtc))
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_TIMEOUT K_SECONDS(20)

static atomic_t callbacks;
static atomic_t callback_ids;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id < 2U) {
		atomic_or(&callback_ids, BIT(id));
	}
	atomic_inc(&callbacks);
}

ZTEST(rtc_alarm_api, test_both_alarm_channels)
{
	struct rtc_time now = {
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
	const struct rtc_time alarm = {
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
	struct rtc_time observed;

	zassert_true(device_is_ready(RTC_DEVICE), "RTC device is not ready");
	atomic_clear(&callbacks);
	atomic_clear(&callback_ids);

	zassert_ok(rtc_set_time(RTC_DEVICE, &now), "rtc_set_time failed");
	for (uint16_t id = 0; id < 2; id++) {
		zassert_ok(rtc_alarm_set_callback(RTC_DEVICE, id, alarm_callback, NULL),
			  "setting callback for alarm %u failed", id);
		zassert_ok(rtc_alarm_set_time(RTC_DEVICE, id, ALARM_MASK, &alarm),
			  "setting alarm %u failed", id);
	}

	k_sleep(K_SECONDS(2));
	zassert_equal(atomic_get(&callbacks), 0,
		      "alarm callback reported before configured time");
	for (uint16_t id = 0; id < 2; id++) {
		bool pending = true;

		zassert_ok(rtc_alarm_is_pending(RTC_DEVICE, id, &pending),
			  "checking alarm %u failed", id);
		zassert_false(pending, "alarm %u pending prematurely", id);
	}

	/* The target is ten seconds after the programmed calendar time. */
	zassert_ok(rtc_alarm_is_pending(RTC_DEVICE, 0, &(bool){ false }),
		  "RTC alarm API became unavailable");
	for (int elapsed = 0; elapsed < 10; elapsed++) {
		k_sleep(K_SECONDS(1));
		if (atomic_get(&callbacks) == 2) {
			break;
		}
	}
	zassert_equal(atomic_get(&callbacks), 2,
		      "both alarms did not fire within 12 seconds");
	zassert_equal(atomic_get(&callback_ids), BIT(0) | BIT(1),
		      "callbacks did not identify both configured alarm IDs");
	zassert_ok(rtc_get_time(RTC_DEVICE, &observed), "rtc_get_time failed");
	zassert_equal(observed.tm_year, 125, "unexpected RTC year");
	zassert_equal(observed.tm_mon, 0, "unexpected RTC month");
	zassert_equal(observed.tm_mday, 1, "unexpected RTC day");
	zassert_equal(observed.tm_hour, 0, "unexpected RTC hour");
	zassert_equal(observed.tm_min, 0, "unexpected RTC minute");
	zassert_equal(observed.tm_sec, 5, "unexpected RTC alarm time");
}

ZTEST_SUITE(rtc_alarm_api, NULL, NULL, NULL, NULL, NULL);
