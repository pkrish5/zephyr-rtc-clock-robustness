#include <zephyr/atomic.h>
#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_COUNT 2
#define ALARM_TIMEOUT K_SECONDS(21)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem alarm_sem;
static atomic_t callback_count;
static atomic_t callback_ids;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id < ALARM_COUNT) {
		atomic_or(&callback_ids, BIT(id));
		atomic_inc(&callback_count);
		k_sem_give(&alarm_sem);
	}
}

static bool time_has_reached_alarm(const struct rtc_time *time)
{
	return time->tm_year > 125 ||
	       (time->tm_year == 125 &&
		(time->tm_mon > 0 ||
		 (time->tm_mon == 0 &&
		  (time->tm_mday > 1 ||
		   (time->tm_mday == 1 &&
		    (time->tm_hour > 0 ||
		     (time->tm_hour == 0 &&
		      (time->tm_min > 0 ||
		       (time->tm_min == 0 && time->tm_sec >= 5)))))))));
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
	struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	};
	struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time now;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	k_sem_init(&alarm_sem, 0, ALARM_COUNT);
	atomic_set(&callback_count, 0);
	atomic_set(&callback_ids, 0);

	zassert_ok(rtc_set_time(rtc, &start), "Could not set RTC calendar");
	for (uint16_t id = 0; id < ALARM_COUNT; id++) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback, NULL),
			   "Could not install callback for alarm %u", id);
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
			   "Could not set alarm %u", id);
	}

	/* Wait until the calendar reaches 00:00:04, checking it never fires early.
	 * At 17 kHz with a 128 x 250 prescaler, one RTC second can take
	 * about 1.883 s; 21 s covers the ten-second interval plus margin.
	 */
	int64_t deadline = k_uptime_get() + k_ticks_to_ms_ceil32(ALARM_TIMEOUT);
	while (true) {
		zassert_equal(atomic_get(&callback_count), 0,
			      "Alarm callback fired before the configured time");
		zassert_ok(rtc_get_time(rtc, &now), "Could not read RTC calendar");
		if (time_has_reached_alarm(&now)) {
			break;
		}
		zassert_true(k_uptime_get() < deadline,
			     "RTC did not reach the alarm time within the bound");
		k_sleep(K_MSEC(20));
	}

	for (int i = 0; i < ALARM_COUNT; i++) {
		zassert_ok(k_sem_take(&alarm_sem, K_SECONDS(2)),
			   "Timed out waiting for alarm callback %d", i);
	}
	zassert_equal(atomic_get(&callback_count), ALARM_COUNT,
		      "Unexpected number of alarm callbacks");
	zassert_equal(atomic_get(&callback_ids), BIT(0) | BIT(1),
		      "Callbacks did not identify both configured alarm channels");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
