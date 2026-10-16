#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_A 0
#define ALARM_B 1
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | RTC_ALARM_TIME_MASK_MINUTE | \
		RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_BITS ((1U << ALARM_A) | (1U << ALARM_B))

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_bits;

static void alarm_callback(const struct device *dev, uint16_t alarm_id,
			   void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (alarm_id == ALARM_A || alarm_id == ALARM_B) {
		atomic_or(&callback_bits, (atomic_val_t)(1U << alarm_id));
	}
}

ZTEST(rtc_alarm, test_both_alarms)
{
	struct rtc_time now = {0};
	const struct rtc_time start = {
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

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&callback_bits, 0);
	zassert_ok(rtc_set_time(rtc, &start), "Failed to set RTC time");
	zassert_ok(rtc_alarm_set_callback(rtc, ALARM_A, alarm_callback, NULL),
		   "Failed to configure callback A");
	zassert_ok(rtc_alarm_set_callback(rtc, ALARM_B, alarm_callback, NULL),
		   "Failed to configure callback B");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_A, ALARM_MASK, &alarm),
		   "Failed to configure alarm A");
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_B, ALARM_MASK, &alarm),
		   "Failed to configure alarm B");

	/* The target is ten seconds away; both callbacks must remain quiet at 23:59:55. */
	zassert_ok(rtc_get_time(rtc, &now), "Failed to read RTC time");
	zassert_equal(now.tm_year, 124);
	zassert_equal(now.tm_mon, 11);
	zassert_equal(now.tm_mday, 31);
	zassert_equal(now.tm_hour, 23);
	zassert_equal(now.tm_min, 59);
	zassert_equal(now.tm_sec, 55);
	zassert_equal(atomic_get(&callback_bits), 0, "Alarm callback fired prematurely");
	zassert_false(rtc_alarm_is_pending(rtc, ALARM_A), "Alarm A is pending early");
	zassert_false(rtc_alarm_is_pending(rtc, ALARM_B), "Alarm B is pending early");

	/* Allow three times the ten-second interval for LSI/driver scheduling tolerance. */
	for (int i = 0; i < 300 && atomic_get(&callback_bits) != ALARM_BITS; i++) {
		k_sleep(K_MSEC(100));
	}

	zassert_equal(atomic_get(&callback_bits), ALARM_BITS,
		      "Timed out waiting for both alarm IDs");
	zassert_ok(rtc_get_time(rtc, &now), "Failed to read RTC time after alarms");
	zassert_true(now.tm_year > 125 ||
		     (now.tm_year == 125 &&
		      (now.tm_mon > 0 ||
		       (now.tm_mon == 0 &&
			(now.tm_mday > 1 ||
			 (now.tm_mday == 1 &&
			  (now.tm_hour > 0 ||
			   (now.tm_hour == 0 &&
			    (now.tm_min > 0 ||
			     (now.tm_min == 0 && now.tm_sec >= 5)))))))))),
		      "Callbacks observed before configured alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
