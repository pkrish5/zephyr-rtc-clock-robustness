#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_ID_0 0U
#define ALARM_ID_1 1U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

/*
 * Ten calendar seconds can take about 18.824 wall seconds at the minimum
 * documented LSI rate. The 30-second deadline allows that arrival time plus
 * an 11-second test-policy margin for interrupt and thread scheduling.
 */
#define CALLBACK_DEADLINE K_SECONDS(30)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem callback_sem;
static atomic_t callback_bits;
static atomic_t callback_id_error;

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id == ALARM_ID_0) {
		atomic_set_bit(&callback_bits, 0);
	} else if (id == ALARM_ID_1) {
		atomic_set_bit(&callback_bits, 1);
	} else {
		atomic_set(&callback_id_error, 1);
	}

	k_sem_give(&callback_sem);
}

ZTEST(rtc_alarm_callbacks, test_both_alarm_channels)
{
	struct rtc_time now = {0};
	struct rtc_time alarm = {
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
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	k_sem_init(&callback_sem, 0, 2);
	atomic_clear(&callback_bits);
	atomic_clear(&callback_id_error);

	/* Disarm previous alarm state before installing this test's callbacks. */
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_0, NULL, NULL);
	zassert_true(ret == 0 || ret == -ENOTSUP,
		     "Could not clear alarm 0 callback: %d", ret);
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_1, NULL, NULL);
	zassert_true(ret == 0 || ret == -ENOTSUP,
		     "Could not clear alarm 1 callback: %d", ret);

	ret = rtc_set_time(rtc, &(struct rtc_time) {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
		.tm_wday = 2,
		.tm_yday = 365,
		.tm_isdst = -1,
	});
	zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);

	ret = rtc_alarm_set_callback(rtc, ALARM_ID_0, alarm_callback, NULL);
	zassert_equal(ret, 0, "Could not set alarm 0 callback: %d", ret);
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_1, alarm_callback, NULL);
	zassert_equal(ret, 0, "Could not set alarm 1 callback: %d", ret);

	ret = rtc_alarm_set_time(rtc, ALARM_ID_0, ALARM_MASK, &alarm);
	zassert_equal(ret, 0, "Could not set alarm 0 time: %d", ret);
	ret = rtc_alarm_set_time(rtc, ALARM_ID_1, ALARM_MASK, &alarm);
	zassert_equal(ret, 0, "Could not set alarm 1 time: %d", ret);

	/* Allow five calendar seconds to pass and verify neither fired early. */
	k_sleep(K_SECONDS(3));
	ret = rtc_get_time(rtc, &now);
	zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);
	zassert_true(now.tm_year == 124 && now.tm_mon == 11 &&
		     now.tm_mday == 31 && now.tm_hour == 23 &&
		     now.tm_min == 59 && now.tm_sec < 5,
		     "RTC did not remain before alarm time");
	zassert_equal(atomic_get(&callback_bits), 0,
		      "Alarm callback fired before configured time");
	zassert_equal(atomic_get(&callback_id_error), 0,
		      "Callback reported an unexpected alarm ID");
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_0);
	zassert_equal(ret, 0, "Alarm 0 pending before time: %d", ret);
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_1);
	zassert_equal(ret, 0, "Alarm 1 pending before time: %d", ret);

	/* Wait for each callback against one finite total delivery deadline. */
	{
		int64_t deadline = k_uptime_get() + CALLBACK_DEADLINE.ticks;
		uint32_t observed = 0U;

		while (observed != 2U) {
			int64_t remaining = deadline - k_uptime_get();

			zassert_true(remaining > 0,
				     "Timed out waiting for both RTC alarm callbacks");
			zassert_equal(k_sem_take(&callback_sem,
						 K_TICKS(remaining)), 0,
				      "Timed out waiting for RTC alarm callback");
			observed++;
		}
	}

	zassert_equal(atomic_get(&callback_id_error), 0,
		      "Callback reported an unexpected alarm ID");
	zassert_equal(atomic_get(&callback_bits), BIT(0) | BIT(1),
		      "Expected callbacks from alarm IDs 0 and 1");
	ret = rtc_get_time(rtc, &now);
	zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);
	zassert_true(now.tm_year == 125 && now.tm_mon == 0 &&
		     now.tm_mday == 1 && now.tm_hour == 0 &&
		     now.tm_min == 0 && now.tm_sec >= 5,
		     "Callbacks arrived before configured RTC alarm time");
}

ZTEST_SUITE(rtc_alarm_callbacks, NULL, NULL, NULL, NULL, NULL);
