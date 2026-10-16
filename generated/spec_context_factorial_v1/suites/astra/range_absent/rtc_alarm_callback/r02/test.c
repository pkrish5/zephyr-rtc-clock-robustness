#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_COUNT 2
#define WAIT_LIMIT_MS 30000
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

struct observation {
	struct k_sem ready;
	atomic_t calls;
	uint16_t id;
	int read_result;
	struct rtc_time time;
};

static struct observation observations[ALARM_COUNT];

static void alarm_callback(const struct device *dev, uint16_t id, void *data)
{
	struct observation *obs = data;

	/* Preserve the first event, including an unexpectedly early event. */
	if (atomic_inc(&obs->calls) == 0) {
		obs->id = id;
		/* STM32F407 reads the RTC registers without blocking. */
		obs->read_result = rtc_get_time(dev, &obs->time);
		k_sem_give(&obs->ready);
	}
}

ZTEST(rtc_rollover, test_both_alarm_channels)
{
	struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
		.tm_nsec = 0,
	};
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
			   "Cannot disable alarm %u", (unsigned int)id);
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL),
			   "Cannot clear callback");
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0,
			     "Cannot clear pending alarm");
		k_sem_init(&observations[id].ready, 0, 1);
		atomic_set(&observations[id].calls, 0);
	}

	zassert_ok(rtc_set_time(rtc, &start), "Cannot set calendar");
	/*
	 * Ten RTC seconds cross midnight. Allow 30 wall-clock seconds:
	 * a nominal 32 kHz LSI running at its 17 kHz minimum needs about
	 * 19 seconds, leaving ample scheduling and tick-phase margin.
	 * Both channels share this deadline; no unbounded wait is used.
	 */
	deadline = k_uptime_get() + WAIT_LIMIT_MS;

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						 &observations[id]),
			   "Cannot register callback");
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &target),
			   "Cannot configure alarm %u", (unsigned int)id);
	}

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		int64_t remaining = deadline - k_uptime_get();

		zassert_true(remaining > 0, "Alarm deadline expired");
		zassert_ok(k_sem_take(&observations[id].ready,
				     K_MSEC(remaining)),
			   "Alarm %u did not fire", (unsigned int)id);
	}

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
			   "Cannot disable alarm");
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL),
			   "Cannot remove callback");
	}

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		const struct observation *obs = &observations[id];

		/* Semaphore acquisition publishes the callback's saved data. */
		zassert_equal(atomic_get(&obs->calls), 1,
			      "Unexpected callback count");
		zassert_equal(obs->id, id, "Callback reported wrong alarm ID");
		zassert_ok(obs->read_result, "Callback could not read RTC");
		/*
		 * Checking the first callback's own timestamp detects premature
		 * delivery, even if this thread does not run until after midnight.
		 */
		zassert_true(obs->time.tm_year == target.tm_year &&
			     obs->time.tm_mon == target.tm_mon &&
			     obs->time.tm_mday == target.tm_mday &&
			     obs->time.tm_hour == target.tm_hour &&
			     obs->time.tm_min == target.tm_min &&
			     obs->time.tm_sec == target.tm_sec,
			     "Alarm %u fired prematurely or outside target second",
			     (unsigned int)id);
	}
}

ZTEST_SUITE(rtc_rollover, NULL, NULL, NULL, NULL, NULL);
