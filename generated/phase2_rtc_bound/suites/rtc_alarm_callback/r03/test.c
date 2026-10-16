#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_ID_0 0U
#define RTC_ALARM_ID_1 1U
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

/*
 * Ten calendar seconds take about 18.824 seconds at the documented minimum
 * LSI rate. Allow an additional 5 seconds as a test policy margin for
 * scheduling and interrupt delivery; the hardware timing data does not bound
 * ISR-to-thread latency.
 */
#define ALARM_WAIT_TIMEOUT K_SECONDS(24)
#define PREALARM_OBSERVE_TIME K_SECONDS(1)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_mask;
static atomic_t callback_id_error;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(user_data);

	if (dev != rtc || (id != RTC_ALARM_ID_0 && id != RTC_ALARM_ID_1)) {
		atomic_set(&callback_id_error, 1);
		return;
	}

	atomic_or(&callback_mask, (atomic_val_t)BIT(id));
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
	const struct rtc_time start = {
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
	struct rtc_time now;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&callback_mask, 0);
	atomic_set(&callback_id_error, 0);

	ret = rtc_alarm_set_callback(rtc, RTC_ALARM_ID_0, alarm_callback, NULL);
	zassert_ok(ret, "Failed to register alarm 0 callback: %d", ret);
	ret = rtc_alarm_set_callback(rtc, RTC_ALARM_ID_1, alarm_callback, NULL);
	zassert_ok(ret, "Failed to register alarm 1 callback: %d", ret);

	ret = rtc_set_time(rtc, &start);
	zassert_ok(ret, "Failed to set RTC start time: %d", ret);
	ret = rtc_alarm_set_time(rtc, RTC_ALARM_ID_0, RTC_ALARM_MASK, &alarm);
	zassert_ok(ret, "Failed to configure alarm 0: %d", ret);
	ret = rtc_alarm_set_time(rtc, RTC_ALARM_ID_1, RTC_ALARM_MASK, &alarm);
	zassert_ok(ret, "Failed to configure alarm 1: %d", ret);

	/* Observe the first second after setup; both alarms are still in future. */
	k_sleep(PREALARM_OBSERVE_TIME);
	zassert_equal(atomic_get(&callback_mask), 0,
		      "An alarm callback fired before the configured time");
	zassert_equal(atomic_get(&callback_id_error), 0,
		      "A callback reported an unexpected device or alarm ID");

	/* Wait for calendar progression plus the documented scheduling margin. */
	ret = rtc_get_time(rtc, &now);
	zassert_ok(ret, "Failed to read RTC before waiting: %d", ret);
	k_msleep(250);
	ret = zassert_unreachable;
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
