#include <zephyr/atomic.h>
#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_COUNT 2
#define ALARM_WAIT_MS 25000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_mask;
static atomic_t unexpected_id;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id < ALARM_COUNT) {
		atomic_or(&callback_mask, BIT(id));
	} else {
		atomic_set(&unexpected_id, 1);
	}
}

static bool rtc_time_at_or_after_alarm(const struct rtc_time *time)
{
	/* rtc_time.tm_year is years since 1900 and tm_mon is zero based. */
	if (time->tm_year != 125 || time->tm_mon != 0) {
		return time->tm_year > 125 ||
		       (time->tm_year == 125 && time->tm_mon > 0);
	}
	if (time->tm_mday != 1) {
		return time->tm_mday > 1;
	}
	if (time->tm_hour != 0) {
		return time->tm_hour > 0;
	}
	if (time->tm_min != 0) {
		return time->tm_min > 0;
	}
	return time->tm_sec >= 5;
}

ZTEST(rtc_alarm, test_both_alarm_callbacks)
{
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
	struct rtc_time now;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&callback_mask, 0);
	atomic_set(&unexpected_id, 0);

	zassert_ok(rtc_set_time(rtc, &start), "Could not set RTC calendar");
	for (uint16_t id = 0; id < ALARM_COUNT; id++) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback, NULL),
			   "Could not register callback for alarm %u", id);
		zassert_ok(rtc_alarm_set_time(rtc, id, &alarm, ALARM_MASK),
			   "Could not set alarm %u", id);
	}

	/* The target is ten calendar seconds away; even at 47 kHz this
	 * prescaler needs about 6.8 real seconds to reach it.
	 */
	k_sleep(K_SECONDS(1));
	zassert_equal(atomic_get(&callback_mask), 0,
		      "An alarm callback fired before the alarm time");
	zassert_equal(atomic_get(&unexpected_id), 0, "Unexpected alarm ID");
	for (uint16_t id = 0; id < ALARM_COUNT; id++) {
		zassert_false(rtc_alarm_is_pending(rtc, id),
			      "Alarm %u became pending prematurely", id);
	}

	/* At 17 kHz, ten RTC seconds take at most about 18.9 real seconds.
	 * The 25-second deadline allows several more seconds for thread/ISR
	 * delivery, whose latency is not specified by the oscillator bound.
	 */
	int64_t deadline = k_uptime_get() + ALARM_WAIT_MS;
	while (atomic_get(&callback_mask) != BIT(0) + BIT(1) &&
	       k_uptime_get() < deadline) {
		k_sleep(K_MSEC(20));
	}

	zassert_equal(atomic_get(&callback_mask), BIT(0) + BIT(1),
		      "Both alarm callbacks did not fire before the deadline");
	zassert_equal(atomic_get(&unexpected_id), 0, "Unexpected alarm ID");
	zassert_ok(rtc_get_time(rtc, &now), "Could not read RTC calendar");
	zassert_true(rtc_time_at_or_after_alarm(&now),
		     "Callbacks fired before RTC reached 2025-01-01 00:00:05");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
