#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
BUILD_ASSERT(ALARM_MASK == 7);

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static uint16_t channel_ids[2] = { 0, 1 };
static atomic_t queue_overflow;

struct alarm_event {
	uint16_t configured_id;
	uint16_t reported_id;
	int read_result;
	struct rtc_time observed_time;
};

K_MSGQ_DEFINE(events, sizeof(struct alarm_event), 8, 4);

static const struct rtc_time start_time = {
	.tm_year = 2024 - 1900, .tm_mon = 12 - 1, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1, .tm_nsec = 0,
};

static const struct rtc_time alarm_time = {
	.tm_year = 2025 - 1900, .tm_mon = 1 - 1, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1, .tm_nsec = 0,
};

/* Compare calendar fields; weekday, DST and subsecond data are irrelevant. */
static int calendar_compare(const struct rtc_time *a,
			    const struct rtc_time *b)
{
	const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
			   a->tm_hour, a->tm_min, a->tm_sec };
	const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
			   b->tm_hour, b->tm_min, b->tm_sec };

	for (unsigned int i = 0; i < ARRAY_SIZE(av); ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct alarm_event event = {
		.configured_id = *(const uint16_t *)user_data,
		.reported_id = id,
	};

	/*
	 * The STM32 RTC calendar read uses hardware register reads. Sample in
	 * the callback so thread scheduling delay cannot change the observation.
	 * Publish a copy through an ISR-safe queue; never assert in the ISR.
	 */
	event.read_result = rtc_get_time(dev, &event.observed_time);
	if (k_msgq_put(&events, &event, K_NO_WAIT) != 0) {
		atomic_set(&queue_overflow, 1);
	}
}

static void stop_alarms(void *fixture)
{
	ARG_UNUSED(fixture);
	if (!device_is_ready(rtc)) {
		return;
	}
	for (uint16_t id = 0; id < 2; ++id) {
		(void)rtc_alarm_set_callback(rtc, id, NULL, NULL);
		(void)rtc_alarm_set_time(rtc, id, 0, NULL);
	}
}

ZTEST(rtc_rollover, test_both_alarm_channels)
{
	struct rtc_time now;
	struct alarm_event event;
	unsigned int seen = 0;

	zassert_true(device_is_ready(rtc), "RTC is not ready");

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		/* This API also clears any retained pending indication. */
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0);
	}
	k_msgq_purge(&events);
	atomic_clear(&queue_overflow);

	/*
	 * Ten calendar seconds take at most 10 * 32000 / 17000 = 18.824
	 * wall seconds with the specified LSI and prescaler. Use a shared
	 * 30-second deadline, including setup and callback delivery. The
	 * remaining roughly 11 seconds are an explicit test liveness budget,
	 * not an ISR/thread latency guarantee derived from oscillator limits.
	 */
	const int64_t deadline = k_uptime_get() + 30000;

	zassert_ok(rtc_set_time(rtc, &start_time));
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						&channel_ids[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time));
	}

	zassert_ok(rtc_get_time(rtc, &now));
	zassert_true(calendar_compare(&now, &alarm_time) < 0,
		     "Setup did not finish before the alarm time");

	while (seen != BIT_MASK(2)) {
		int64_t remaining = deadline - k_uptime_get();

		zassert_true(remaining > 0, "Alarm deadline expired; seen=%u", seen);
		zassert_ok(k_msgq_get(&events, &event, K_MSEC(remaining)),
			   "Missing callback; seen=%u", seen);
		zassert_false(atomic_get(&queue_overflow), "Callback queue overflow");
		zassert_ok(event.read_result, "Callback calendar read failed");
		zassert_true(event.configured_id < 2, "Invalid callback context");
		zassert_equal(event.reported_id, event.configured_id,
			      "Callback reported the wrong alarm ID");
		zassert_false(seen & BIT(event.configured_id), "Duplicate callback");

		/* Every callback is checked, including any queued during setup. */
		int comparison = calendar_compare(&event.observed_time, &alarm_time);

		zassert_true(comparison >= 0, "Alarm %u fired prematurely",
			     event.configured_id);
		zassert_equal(comparison, 0,
			      "Alarm %u was not observed at the configured RTC second",
			      event.configured_id);
		seen |= BIT(event.configured_id);
	}

	stop_alarms(NULL);
	zassert_false(atomic_get(&queue_overflow), "Callback queue overflow");
	zassert_equal(k_msgq_num_used_get(&events), 0, "Unexpected extra callback");
}

ZTEST_SUITE(rtc_rollover, NULL, NULL, NULL, stop_alarms, NULL);
