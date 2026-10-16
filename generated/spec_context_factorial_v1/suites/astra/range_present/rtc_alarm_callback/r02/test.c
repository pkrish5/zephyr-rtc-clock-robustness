#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define ALARM_COUNT 2
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define TIMEOUT_MS 30000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static const struct rtc_time start_time = {
	.tm_year = 2024 - 1900, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1, .tm_nsec = 0,
};

static const struct rtc_time alarm_time = {
	.tm_year = 2025 - 1900, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1, .tm_nsec = 0,
};

struct observation {
	atomic_t count;
	struct rtc_time time;
	int time_result;
	uint16_t reported_id;
};

static struct observation observations[ALARM_COUNT];

static int calendar_compare(const struct rtc_time *a,
			    const struct rtc_time *b)
{
	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday,
			  a->tm_hour, a->tm_min, a->tm_sec};
	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday,
			  b->tm_hour, b->tm_min, b->tm_sec};

	for (unsigned int i = 0; i < sizeof(av) / sizeof(av[0]); ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct observation *o = user_data;

	if (atomic_get(&o->count) == 0) {
		o->reported_id = id;
		/* STM32F407 rtc_get_time reads the on-chip calendar registers.
		 * Sample here so thread wake-up latency cannot hide an early
		 * callback or falsely make an on-time callback appear late.
		 */
		o->time_result = rtc_get_time(dev, &o->time);
	}
	/* Publish the immutable first-callback record after filling it. */
	atomic_inc(&o->count);
}

ZTEST(rtc_rollover, test_both_alarm_channels)
{
	struct rtc_time now;
	bool completed = false;
	bool observed_before = false;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		atomic_set(&observations[id].count, 0);
	}

	zassert_ok(rtc_set_time(rtc, &start_time));

	/* Ten RTC seconds require at most 10 * 32000 / 17000 = 18.824
	 * real seconds at the documented LSI minimum frequency. The
	 * 30-second deadline adds an explicit test service budget for
	 * setup, interrupt handling and thread scheduling. That margin
	 * is a test requirement, not a latency guarantee from the LSI
	 * specification. Exact callback calendar time is checked separately.
	 */
	const int64_t deadline = k_uptime_get() + TIMEOUT_MS;

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						&observations[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time));
	}

	while (k_uptime_get() < deadline) {
		/* Read counts before the calendar: a callback arriving after
		 * the calendar read must not cause a false premature failure.
		 */
		atomic_val_t c0 = atomic_get(&observations[0].count);
		atomic_val_t c1 = atomic_get(&observations[1].count);

		zassert_ok(rtc_get_time(rtc, &now));
		if (calendar_compare(&now, &alarm_time) < 0) {
			observed_before = true;
			zassert_equal(c0, 0, "Alarm 0 callback was premature");
			zassert_equal(c1, 0, "Alarm 1 callback was premature");
		}
		if (c0 != 0 && c1 != 0) {
			completed = true;
			break;
		}
		k_sleep(K_MSEC(1));
	}

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
	}

	zassert_true(observed_before, "Setup missed the pre-alarm interval");
	zassert_true(completed, "Both callbacks were not observed within 30 s");
	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		const struct observation *o = &observations[id];

		zassert_equal(atomic_get(&o->count), 1,
			      "Alarm %u callback count is not one", (unsigned int)id);
		zassert_equal(o->reported_id, id,
			      "Alarm %u reported the wrong ID", (unsigned int)id);
		zassert_ok(o->time_result, "Callback calendar read failed");
		zassert_equal(calendar_compare(&o->time, &alarm_time), 0,
			      "Alarm %u callback was early or late", (unsigned int)id);
	}
}

ZTEST_SUITE(rtc_rollover, NULL, NULL, NULL, NULL, NULL);
