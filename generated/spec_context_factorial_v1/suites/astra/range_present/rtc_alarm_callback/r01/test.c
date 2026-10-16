#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define WATCHDOG_MS 25000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
K_SEM_DEFINE(events, 0, 2);

struct observation {
	atomic_t calls;
	uint16_t id;
	const struct device *dev;
	int read_result;
	struct rtc_time time;
};

static struct observation observed[2];

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct observation *o = user_data;

	/* Preserve the first event, including an unexpectedly early event. */
	if (atomic_inc(&o->calls) != 0) {
		return;
	}
	o->dev = dev;
	o->id = id;
	/* STM32's calendar read samples hardware without waiting for a tick. */
	o->read_result = rtc_get_time(dev, &o->time);
	/* Publish the complete snapshot to the test thread. */
	k_sem_give(&events);
}

ZTEST(rtc_alarm, test_year_rollover)
{
	struct rtc_time start = {
		.tm_year = 2024 - 1900, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	};
	struct rtc_time alarm = {
		.tm_year = 2025 - 1900, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	};
	int64_t deadline;
	int received = 0;

	zassert_true(device_is_ready(rtc), "RTC alias is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm field mask");

	k_sem_reset(&events);
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, &alarm));
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0);
		atomic_set(&observed[id].calls, 0);
	}

	zassert_ok(rtc_set_time(rtc, &start));
	deadline = k_uptime_get() + WATCHDOG_MS;
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						&observed[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm));
	}

	/*
	 * Ten calendar seconds require at most 10 * 32000 / 17000 =
	 * 18.824 real seconds. At 47 kHz they require about 6.809 seconds;
	 * therefore a ten-second wall-clock sleep cannot test prematurity.
	 *
	 * The 25-second watchdog includes over six seconds of operational
	 * margin. This is a finite test responsiveness requirement, NOT an
	 * ISR-delivery bound inferred from the oscillator specification.
	 * Callback snapshots independently require delivery during second 05;
	 * even a callback received before the watchdog fails if delivered late.
	 */
	while (received < 2) {
		int64_t remaining = deadline - k_uptime_get();

		if (remaining <= 0 ||
		    k_sem_take(&events, K_MSEC(remaining)) != 0) {
			break;
		}
		++received;
	}

	/* Stop sources before assertions, including on the timeout path. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, &alarm));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
	}

	zassert_equal(received, 2, "Both callbacks must arrive within 25 s");
	for (uint16_t id = 0; id < 2; ++id) {
		const struct observation *o = &observed[id];

		zassert_equal(atomic_get(&o->calls), 1,
			      "Alarm %u callback count", (unsigned int)id);
		zassert_equal(o->dev, rtc, "Unexpected callback device");
		zassert_equal(o->id, id, "Unexpected callback alarm ID");
		zassert_ok(o->read_result, "Callback calendar read failed");
		/* Exact calendar equality rejects both premature and late events. */
		zassert_true(o->time.tm_year == alarm.tm_year &&
			     o->time.tm_mon == alarm.tm_mon &&
			     o->time.tm_mday == alarm.tm_mday &&
			     o->time.tm_hour == alarm.tm_hour &&
			     o->time.tm_min == alarm.tm_min &&
			     o->time.tm_sec == alarm.tm_sec,
			     "Alarm %u fired outside 2025-01-01 00:00:05",
			     (unsigned int)id);
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
