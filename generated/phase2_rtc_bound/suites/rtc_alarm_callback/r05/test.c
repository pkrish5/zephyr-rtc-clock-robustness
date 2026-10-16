#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_ID_0 0U
#define ALARM_ID_1 1U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

/* Calendar arrival can take 18.824 s at the documented minimum LSI rate.
 * Allow 5 s of additional scheduling/interrupt-delivery margin by policy.
 */
#define CALLBACK_DEADLINE K_SECONDS(24)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_bits;
static atomic_t unexpected_callback;
static struct k_sem callbacks_done;

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	ARG_UNUSED(user_data);
	if (dev != rtc || (id != ALARM_ID_0 && id != ALARM_ID_1)) {
		atomic_set(&unexpected_callback, 1);
		k_sem_give(&callbacks_done);
		return;
	}

	atomic_or(&callback_bits, BIT(id));
	k_sem_give(&callbacks_done);
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
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
	struct rtc_time observed;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&callback_bits, 0);
	atomic_set(&unexpected_callback, 0);
	k_sem_init(&callbacks_done, 0, 2);

	ret = rtc_set_time(rtc, &now);
	zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_0, alarm_callback, NULL);
	zassert_equal(ret, 0, "setting callback 0 failed: %d", ret);
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_1, alarm_callback, NULL);
	zassert_equal(ret, 0, "setting callback 1 failed: %d", ret);
	ret = rtc_alarm_set_time(rtc, ALARM_ID_0, ALARM_MASK, &alarm);
	zassert_equal(ret, 0, "setting alarm 0 failed: %d", ret);
	ret = rtc_alarm_set_time(rtc, ALARM_ID_1, ALARM_MASK, &alarm);
	zassert_equal(ret, 0, "setting alarm 1 failed: %d", ret);

	/* Check absence of callbacks and pending alarms before calendar arrival. */
	k_sleep(K_SECONDS(2));
	zassert_equal(atomic_get(&callback_bits), 0,
		      "callback observed before alarm time");
	zassert_equal(atomic_get(&unexpected_callback), 0,
		      "unexpected callback before alarm time");
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_0);
	zassert_equal(ret, 0, "alarm 0 unexpectedly pending: %d", ret);
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_1);
	zassert_equal(ret, 0, "alarm 1 unexpectedly pending: %d", ret);

	/* The 24 s deadline covers 18.824 s worst-case calendar arrival plus
	 * the documented 5 s policy margin for scheduling and delivery.
	 */
	zassert_equal(k_sem_take(&callbacks_done, CALLBACK_DEADLINE), 0,
		      "no alarm callback by deadline");
	zassert_equal(k_sem_take(&callbacks_done, K_NO_WAIT), 0,
		      "second alarm callback was not delivered");
	zassert_equal(atomic_get(&unexpected_callback), 0,
		      "callback reported invalid device or alarm ID");
	zassert_equal(atomic_get(&callback_bits), BIT(ALARM_ID_0) | BIT(ALARM_ID_1),
		      "callbacks did not identify both configured channels");

	ret = rtc_get_time(rtc, &observed);
	zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);
	zassert_true(observed.tm_year == alarm.tm_year &&
		     observed.tm_mon == alarm.tm_mon &&
		     observed.tm_mday == alarm.tm_mday &&
		     observed.tm_hour == alarm.tm_hour &&
		     observed.tm_min == alarm.tm_min &&
		     observed.tm_sec >= alarm.tm_sec,
		     "callbacks delivered before configured calendar time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
