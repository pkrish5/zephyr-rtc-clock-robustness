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

/* Ten calendar seconds take at most 10 * 32000 / 17000 = 18.824 s.
 * Round up to 19 s and allow another 6 s for setup and software service.
 * That allowance is an executable test deadline, not a hardware-derived
 * ISR or thread latency guarantee. Callback timestamps independently check
 * delivery within the requested calendar second.
 */
#define TEST_TIMEOUT_MS 25000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

struct observation {
	atomic_t calls;
	atomic_t ready;
	uint16_t id;
	int time_rc;
	struct rtc_time time;
};

static struct observation observed[2];

static void alarm_callback(const struct device *dev, uint16_t id,
                           void *user_data)
{
	struct observation *o = user_data;

	/* Preserve the first observation; count unexpected repeat deliveries. */
	if (atomic_inc(&o->calls) != 0) {
		return;
	}
	o->id = id;
	o->time_rc = rtc_get_time(dev, &o->time);
	/* Publish all fields after capturing them, including across ISR return. */
	atomic_set(&o->ready, 1);
}

/* Calendar seconds since the initial time, over this test's short window. */
static int elapsed_calendar_seconds(const struct rtc_time *t)
{
	if (t->tm_year == 124 && t->tm_mon == 11 && t->tm_mday == 31 &&
	    t->tm_hour == 23 && t->tm_min == 59 &&
	    t->tm_sec >= 55 && t->tm_sec <= 59) {
		return t->tm_sec - 55;
	}
	if (t->tm_year == 125 && t->tm_mon == 0 && t->tm_mday == 1 &&
	    t->tm_hour == 0 && t->tm_min == 0 &&
	    t->tm_sec >= 0 && t->tm_sec <= 59) {
		return 5 + t->tm_sec;
	}
	return -1;
}

ZTEST(rtc_alarm, test_both_alarms_across_year_boundary)
{
	const struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	};
	const struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
		.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	};
	struct rtc_time now;
	bool complete = false;

	zassert_true(device_is_ready(rtc), "RTC alias is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm field mask");

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0,
		             "Cannot clear pending alarm %u", (unsigned int)id);
		atomic_clear(&observed[id].calls);
		atomic_clear(&observed[id].ready);
	}

	int64_t deadline = k_uptime_get() + TEST_TIMEOUT_MS;

	zassert_ok(rtc_set_time(rtc, &start));
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
		                                &observed[id]));
		/* Only H:M:S participate in hardware matching. The callback's
		 * full timestamp verifies the expected date rollover as well.
		 */
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &target));
	}

	while (k_uptime_get() < deadline) {
		/* Snapshot events BEFORE reading time: an interrupt between these
		 * operations cannot falsely classify an on-time event as early.
		 */
		atomic_val_t calls0 = atomic_get(&observed[0].calls);
		atomic_val_t calls1 = atomic_get(&observed[1].calls);

		zassert_ok(rtc_get_time(rtc, &now));
		int elapsed = elapsed_calendar_seconds(&now);

		zassert_true(elapsed >= 0, "Unexpected RTC calendar value");
		if (elapsed < 10) {
			zassert_equal(calls0, 0, "Alarm 0 observed prematurely");
			zassert_equal(calls1, 0, "Alarm 1 observed prematurely");
		}
		if (atomic_get(&observed[0].ready) &&
		    atomic_get(&observed[1].ready)) {
			complete = true;
			break;
		}
		k_sleep(K_MSEC(10));
	}

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
	}

	zassert_true(complete, "Both callbacks must complete within 25 seconds");
	for (uint16_t id = 0; id < 2; ++id) {
		const struct observation *o = &observed[id];

		zassert_equal(atomic_get(&o->calls), 1, "Unexpected callback count");
		zassert_equal(o->id, id, "Callback reported the wrong alarm ID");
		zassert_ok(o->time_rc, "Cannot timestamp callback");
		zassert_equal(elapsed_calendar_seconds(&o->time), 10,
		              "Callback was not at 2025-01-01 00:00:05");
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
