#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_ALARM_A 0U
#define RTC_ALARM_B 1U
#define RTC_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)

/* Ten calendar seconds take at most 18.824 s at the documented minimum LSI
 * frequency. Allow a further 5 s for test-thread scheduling and callback
 * delivery; this margin is a test policy, not a hardware ISR latency bound.
 */
#define ALARM_WAIT_BOUND K_SECONDS(24)
#define PREALARM_OBSERVE K_MSEC(250)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_ids;
static atomic_t callback_count;

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id == RTC_ALARM_A) {
		atomic_or(&callback_ids, BIT(0));
	} else if (id == RTC_ALARM_B) {
		atomic_or(&callback_ids, BIT(1));
	}
	atomic_inc(&callback_count);
}

ZTEST(rtc_alarm_callbacks, test_both_alarm_channels)
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
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_clear(&callback_ids);
	atomic_clear(&callback_count);

	ret = rtc_alarm_set_callback(rtc, RTC_ALARM_A, alarm_callback, NULL);
	zassert_ok(ret, "set callback for alarm %u: %d", RTC_ALARM_A, ret);
	ret = rtc_alarm_set_callback(rtc, RTC_ALARM_B, alarm_callback, NULL);
	zassert_ok(ret, "set callback for alarm %u: %d", RTC_ALARM_B, ret);

	ret = rtc_set_time(rtc, &now);
	zassert_ok(ret, "set initial RTC time: %d", ret);
	ret = rtc_alarm_set_time(rtc, RTC_ALARM_A, RTC_ALARM_MASK, &alarm);
	zassert_ok(ret, "set time for alarm %u: %d", RTC_ALARM_A, ret);
	ret = rtc_alarm_set_time(rtc, RTC_ALARM_B, RTC_ALARM_MASK, &alarm);
	zassert_ok(ret, "set time for alarm %u: %d", RTC_ALARM_B, ret);

	k_sleep(PREALARM_OBSERVE);
	zassert_equal(atomic_get(&callback_count), 0,
		      "callback observed before alarm time");
	zassert_equal(atomic_get(&callback_ids), 0,
		      "alarm ID observed before alarm time");

	ret = k_poll_signal_wait; /* placeholder */
	ARG_UNUSED(ret);
	/* Poll protected callback state until both channel IDs arrive. */
	int64_t deadline = k_uptime_get() + ALARM_WAIT_BOUND;
	while (atomic_get(&callback_ids) != (BIT(0) | BIT(1)) &&
	       k_uptime_get() < deadline) {
		k_sleep(K_MSEC(20));
	}

	zassert_equal(atomic_get(&callback_ids), BIT(0) | BIT(1),
		      "did not receive callbacks for both alarm IDs");
	zassert_equal(atomic_get(&callback_count), 2,
		      "expected exactly one callback per alarm channel");

	ret = rtc_get_time(rtc, &now);
	zassert_ok(ret, "read RTC time after callbacks: %d", ret);
	zassert_true(now.tm_year > 125 ||
		     (now.tm_year == 125 &&
		      (now.tm_mon > 0 ||
		       (now.tm_mon == 0 &&
			(now.tm_mday > 1 ||
			 (now.tm_mday == 1 &&
			  (now.tm_hour > 0 ||
			   (now.tm_hour == 0 &&
			    (now.tm_min > 0 ||
			     (now.tm_min == 0 && now.tm_sec >= 5))))))))),
		      "callbacks arrived before configured RTC alarm time");
}

ZTEST_SUITE(rtc_alarm_callbacks, NULL, NULL, NULL, NULL, NULL);
