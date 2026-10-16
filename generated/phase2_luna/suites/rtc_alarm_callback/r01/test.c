#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_WAIT_MS 15000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t alarm_events;
static atomic_t alarm_ids;

static void alarm_callback(const struct device *dev, uint16_t id,
			   uint16_t mask)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(mask);
	if (id < 2U) {
		atomic_or(&alarm_ids, BIT(id));
		atomic_inc(&alarm_events);
	}
}

ZTEST(rtc_alarm, test_both_alarm_callbacks)
{
	struct rtc_time now = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	};
	struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time observed;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&alarm_events, 0);
	atomic_set(&alarm_ids, 0);
	zassert_ok(rtc_alarm_set_callback(rtc, 0, alarm_callback, NULL));
	zassert_ok(rtc_alarm_set_callback(rtc, 1, alarm_callback, NULL));
	zassert_ok(rtc_set_time(rtc, &now));
	zassert_ok(rtc_alarm_set_time(rtc, 0, &alarm, ALARM_MASK));
	zassert_ok(rtc_alarm_set_time(rtc, 1, &alarm, ALARM_MASK));

	k_sleep(K_SECONDS(3));
	zassert_equal(atomic_get(&alarm_events), 0,
		      "Alarm callback observed before configured time");
	zassert_equal(rtc_alarm_is_pending(rtc, 0), 0, "Alarm 0 is premature");
	zassert_equal(rtc_alarm_is_pending(rtc, 1), 0, "Alarm 1 is premature");

	/* The alarm is ten seconds ahead; 15 seconds allows RTC tick and ISR latency. */
	zassert_true(atomic_cas(&alarm_events, 0, 0), "invalid event state");
	for (int i = 0; i < ALARM_WAIT_MS / 10; ++i) {
		if (atomic_get(&alarm_events) >= 2) {
			break;
		}
		k_sleep(K_MSEC(10));
	}
	zassert_equal(atomic_get(&alarm_events), 2,
		      "Both RTC alarm callbacks did not fire within bound");
	zassert_equal(atomic_get(&alarm_ids), BIT(0) | BIT(1),
		      "Callbacks did not report alarm IDs 0 and 1");
	zassert_ok(rtc_get_time(rtc, &observed));
	zassert_equal(observed.tm_year, 125);
	zassert_equal(observed.tm_mon, 0);
	zassert_equal(observed.tm_mday, 1);
	zassert_equal(observed.tm_hour, 0);
	zassert_equal(observed.tm_min, 0);
	zassert_true(observed.tm_sec >= 5, "RTC has not reached alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
