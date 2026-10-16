#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_ID_1 0U
#define ALARM_ID_2 1U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

/* Ten calendar seconds can take up to 18.824 wall seconds at 17 kHz.
 * The 5-second allowance is a test policy margin for scheduling and ISR
 * delivery; the hardware data does not bound callback delivery latency.
 */
#define ARRIVAL_BOUND K_SECONDS(24)
#define DELIVERY_MARGIN K_SECONDS(5)
#define CALLBACK_BOUND (ARRIVAL_BOUND + DELIVERY_MARGIN)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem alarm_sem;
static atomic_t seen_1;
static atomic_t seen_2;
static atomic_t bad_callback;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(user_data);

	if (dev != rtc) {
		atomic_set(&bad_callback, 1);
		return;
	}

	if (id == ALARM_ID_1) {
		atomic_set(&seen_1, 1);
	} else if (id == ALARM_ID_2) {
		atomic_set(&seen_2, 1);
	} else {
		atomic_set(&bad_callback, 1);
		return;
	}

	k_sem_give(&alarm_sem);
}

ZTEST(rtc_alarm, test_two_alarms_at_new_year)
{
	struct rtc_time start = {
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
	struct rtc_time now;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	k_sem_init(&alarm_sem, 0, 2);
	atomic_clear(&seen_1);
	atomic_clear(&seen_2);
	atomic_clear(&bad_callback);

	ret = rtc_alarm_set_callback(rtc, ALARM_ID_1, alarm_callback, NULL);
	zassert_ok(ret, "register alarm 1 callback: %d", ret);
	ret = rtc_alarm_set_callback(rtc, ALARM_ID_2, alarm_callback, NULL);
	zassert_ok(ret, "register alarm 2 callback: %d", ret);

	ret = rtc_set_time(rtc, &start);
	zassert_ok(ret, "set RTC start time: %d", ret);
	ret = rtc_alarm_set_time(rtc, ALARM_ID_1, ALARM_MASK, &alarm);
	zassert_ok(ret, "set alarm 1: %d", ret);
	ret = rtc_alarm_set_time(rtc, ALARM_ID_2, ALARM_MASK, &alarm);
	zassert_ok(ret, "set alarm 2: %d", ret);

	/* Verify the RTC has not reached the configured time and neither
	 * callback nor pending alarm is reported during the pre-alarm sample.
	 */
	k_sleep(K_SECONDS(2));
	ret = rtc_get_time(rtc, &now);
	zassert_ok(ret, "read RTC before alarm: %d", ret);
	zassert_true(now.tm_year == 124 && now.tm_mon == 11 &&
		     now.tm_mday == 31 && now.tm_hour == 23 &&
		     now.tm_min == 59 && now.tm_sec < 5,
		     "RTC advanced past alarm during pre-alarm sample");
	zassert_false(atomic_get(&seen_1) || atomic_get(&seen_2),
		      "callback observed before alarm time");
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_1);
	zassert_equal(ret, 0, "alarm 1 pending before alarm: %d", ret);
	ret = rtc_alarm_is_pending(rtc, ALARM_ID_2);
	zassert_equal(ret, 0, "alarm 2 pending before alarm: %d", ret);

	/* Calendar arrival bound is 18.824 s; 24 s provides 5.176 s of
	 * arrival tolerance. Add 5 s of policy margin for ISR/thread delivery.
	 */
	ret = k_sem_take(&alarm_sem, CALLBACK_BOUND);
	zassert_ok(ret, "alarm 1 callback not delivered by deadline");
	ret = k_sem_take(&alarm_sem, CALLBACK_BOUND);
	zassert_ok(ret, "alarm 2 callback not delivered by deadline");

	zassert_false(atomic_get(&bad_callback), "unexpected callback device or ID");
	zassert_true(atomic_get(&seen_1), "alarm 1 callback was not observed");
	zassert_true(atomic_get(&seen_2), "alarm 2 callback was not observed");
	ret = rtc_get_time(rtc, &now);
	zassert_ok(ret, "read RTC after alarms: %d", ret);
	zassert_true(now.tm_year == 125 && now.tm_mon == 0 &&
		     now.tm_mday == 1 && now.tm_hour == 0 &&
		     now.tm_min == 0 && now.tm_sec >= 5,
		     "callbacks arrived before configured RTC alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
