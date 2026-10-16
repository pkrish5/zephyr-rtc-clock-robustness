#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_DEVICE DEVICE_DT_GET(DT_ALIAS(rtc))
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_TIMEOUT K_SECONDS(15)

static atomic_t fired_mask;
static atomic_t alarm_id[2];

static void alarm_callback(const struct device *dev, uint16_t id,
			   uint32_t status, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(status);
	ARG_UNUSED(user_data);

	if (id < ARRAY_SIZE(alarm_id)) {
		atomic_set(&alarm_id[id], id);
		atomic_or(&fired_mask, BIT(id));
	}
}

ZTEST(rtc_alarm_api, test_both_alarm_callbacks)
{
	const struct device *rtc = RTC_DEVICE;
	struct rtc_time now = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
	};
	const struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
		.tm_mday = 1,
		.tm_mon = 0,
		.tm_year = 125,
	};
	struct rtc_time readback;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&fired_mask, 0);
	atomic_set(&alarm_id[0], -1);
	atomic_set(&alarm_id[1], -1);

	zassert_equal(rtc_set_time(rtc, &now), 0, "rtc_set_time failed");
	zassert_equal(rtc_alarm_set_callback(rtc, 0, alarm_callback, NULL), 0,
		      "alarm 0 callback setup failed");
	zassert_equal(rtc_alarm_set_callback(rtc, 1, alarm_callback, NULL), 0,
		      "alarm 1 callback setup failed");
	zassert_equal(rtc_alarm_set_time(rtc, 0, &alarm, ALARM_MASK), 0,
		      "alarm 0 setup failed");
	zassert_equal(rtc_alarm_set_time(rtc, 1, &alarm, ALARM_MASK), 0,
		      "alarm 1 setup failed");

	k_sleep(K_SECONDS(2));
	zassert_equal(atomic_get(&fired_mask), 0,
		      "an alarm fired before configured time");
	zassert_equal(rtc_get_time(rtc, &readback), 0, "rtc_get_time failed");
	zassert_true(readback.tm_year == 124 && readback.tm_mon == 11 &&
		     readback.tm_mday == 31 && readback.tm_hour == 23 &&
		     readback.tm_min == 59 && readback.tm_sec >= 57 &&
		     readback.tm_sec < 60,
		     "RTC did not remain before the alarm time");

	zassert_ok(k_sleep(ALARM_TIMEOUT), "alarm wait interrupted");
	zassert_equal(atomic_get(&fired_mask), BIT(0) | BIT(1),
		      "both alarm callbacks were not observed");
	zassert_equal(atomic_get(&alarm_id[0]), 0, "alarm 0 reported wrong ID");
	zassert_equal(atomic_get(&alarm_id[1]), 1, "alarm 1 reported wrong ID");
	zassert_equal(rtc_get_time(rtc, &readback), 0, "rtc_get_time failed");
	zassert_true(readback.tm_year == 125 && readback.tm_mon == 0 &&
		     readback.tm_mday == 1 && readback.tm_hour == 0 &&
		     readback.tm_min == 0 && readback.tm_sec >= 5,
		     "callbacks did not occur at or after configured RTC time");
}

ZTEST_SUITE(rtc_alarm_api, NULL, NULL, NULL, NULL, NULL);
