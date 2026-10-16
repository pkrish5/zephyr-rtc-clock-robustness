#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#include <stdint.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

/*
 * Ten RTC seconds take about 19 real seconds at the STM32F407 LSI's
 * 17 kHz minimum, versus its nominal 32 kHz. Allow 30 seconds total.
 */
#define TIMEOUT_MS 30000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

struct alarm_event {
	struct k_sem ready;
	atomic_t calls;
	uint16_t reported_id;
	int read_result;
	struct rtc_time observed;
};

static struct alarm_event events[2];

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct alarm_event *event = user_data;

	/* Only the first invocation writes the record published by ready. */
	if (atomic_inc(&event->calls) != 0) {
		return;
	}

	event->reported_id = id;
	/* The STM32 RTC calendar read is nonblocking, including in its ISR. */
	event->read_result = rtc_get_time(dev, &event->observed);
	k_sem_give(&event->ready);
}

static void check_alarm_time(const struct rtc_time *time)
{
	zassert_equal(time->tm_year, 125, "Callback in wrong year");
	zassert_equal(time->tm_mon, 0, "Callback in wrong month");
	zassert_equal(time->tm_mday, 1, "Callback on wrong day");
	zassert_equal(time->tm_hour, 0, "Callback at wrong hour");
	zassert_equal(time->tm_min, 0, "Callback at wrong minute");
	zassert_true(time->tm_sec >= 5, "Premature callback");
	zassert_equal(time->tm_sec, 5, "Callback missed the alarm second");
}

ZTEST(rtc_alarm, test_two_channels_across_new_year)
{
	struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	int wait_result[2];
	int disable_result[2];
	int unregister_result[2];

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		k_sem_init(&events[id].ready, 0, 1);
		atomic_set(&events[id].calls, 0);
	}

	zassert_ok(rtc_set_time(rtc, &start));
	int64_t deadline = k_uptime_get() + TIMEOUT_MS;

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
					       &events[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
	}

	/*
	 * Each ISR records its own RTC time, so even an early callback that
	 * precedes these waits remains observable. Semaphores publish the
	 * records; both waits share one finite wall-clock deadline.
	 */
	for (uint16_t id = 0; id < 2; ++id) {
		int64_t remaining = deadline - k_uptime_get();

		wait_result[id] = k_sem_take(&events[id].ready,
			remaining > 0 ? K_MSEC(remaining) : K_NO_WAIT);
	}

	/* Quiesce both channels before assertions, including timeout failures. */
	for (uint16_t id = 0; id < 2; ++id) {
		disable_result[id] = rtc_alarm_set_time(rtc, id, 0, NULL);
		unregister_result[id] = rtc_alarm_set_callback(rtc, id, NULL, NULL);
	}

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(disable_result[id]);
		zassert_ok(unregister_result[id]);
		zassert_ok(wait_result[id], "Alarm %u did not arrive within 30 s", id);
		zassert_equal(atomic_get(&events[id].calls), 1,
			      "Unexpected callback count for alarm %u", id);
		zassert_equal(events[id].reported_id, id, "Wrong alarm ID");
		zassert_ok(events[id].read_result, "Callback calendar read failed");
		check_alarm_time(&events[id].observed);
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
