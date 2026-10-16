#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

struct alarm_event {
	uint16_t expected_id;
	uint16_t reported_id;
	struct rtc_time when;
	int read_result;
	atomic_t count;
	struct k_sem fired;
};

static struct alarm_event events[2];

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	struct alarm_event *event = user_data;

	if (atomic_get(&event->count) == 0) {
		event->reported_id = id;
		event->read_result = rtc_get_time(dev, &event->when);
	}
	atomic_inc(&event->count);
	k_sem_give(&event->fired);
}

ZTEST(rtc_alarm, test_both_alarms_across_new_year)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_wday = 2, .tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	};
	const struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_wday = 3, .tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	const uint16_t mask = RTC_ALARM_TIME_MASK_SECOND |
		RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR;
	struct rtc_time now;

	zassert_true(device_is_ready(rtc));
	for (uint16_t id = 0; id < 2; ++id) {
		events[id].expected_id = id;
		atomic_set(&events[id].count, 0);
		k_sem_init(&events[id].fired, 0, 1);
	}

	zassert_ok(rtc_set_time(rtc, &start));
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, mask, &alarm));
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
					  &events[id]));
	}

	/* The alarm is ten RTC seconds away; two seconds leaves ample margin. */
	k_sleep(K_SECONDS(2));
	zassert_ok(rtc_get_time(rtc, &now));
	zassert_true(now.tm_year == 124 && now.tm_mon == 11 &&
		     now.tm_mday == 31 && now.tm_hour == 23 &&
		     now.tm_min == 59 && now.tm_sec < 59);
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_equal(atomic_get(&events[id].count), 0,
			      "alarm fired before midnight");
	}

	/* Fifteen seconds covers the remaining RTC interval and LSI variation. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(k_sem_take(&events[id].fired, K_SECONDS(15)),
			   "alarm callback timed out");
		zassert_equal(events[id].reported_id, events[id].expected_id);
		zassert_ok(events[id].read_result);
		zassert_equal(events[id].when.tm_year, 125);
		zassert_equal(events[id].when.tm_mon, 0);
		zassert_equal(events[id].when.tm_mday, 1);
		zassert_equal(events[id].when.tm_hour, 0);
		zassert_equal(events[id].when.tm_min, 0);
		zassert_equal(events[id].when.tm_sec, 5);
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
