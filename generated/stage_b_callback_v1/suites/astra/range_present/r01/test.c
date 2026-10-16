#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define TEST_TIMEOUT_MS 25000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static K_SEM_DEFINE(completed, 0, 2);

struct observation {
	atomic_t calls;
	uint16_t id;
	int read_result;
	struct rtc_time time;
};

static struct observation observations[2];

static const struct rtc_time start_time = {
	.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
};

static const struct rtc_time alarm_time = {
	.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
};

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct observation *o = user_data;

	/* Preserve the first event, including an incorrectly early event. */
	if (atomic_inc(&o->calls) == 0) {
		o->id = id;
		/* STM32 RTC calendar reads can be performed in this callback. */
		o->read_result = rtc_get_time(dev, &o->time);
		/* Publish the completed record before waking the test thread. */
		k_sem_give(&completed);
	}
}

/* Lexicographic calendar comparison; weekday and derived fields are ignored. */
static int calendar_compare(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday,
			  a->tm_hour, a->tm_min, a->tm_sec};
	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday,
			  b->tm_hour, b->tm_min, b->tm_sec};

	for (unsigned int i = 0; i < ARRAY_SIZE(av); ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

ZTEST(rtc_alarm_callbacks, test_year_rollover)
{
	unsigned int received = 0;
	int disable_result[2];
	int unregister_result[2];

	zassert_true(device_is_ready(rtc), "RTC alias is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
			   "Cannot disable alarm %u", (unsigned int)id);
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL),
			   "Cannot clear callback %u", (unsigned int)id);
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0,
			     "Cannot clear pending alarm %u", (unsigned int)id);
		atomic_set(&observations[id].calls, 0);
	}
	k_sem_reset(&completed);

	zassert_ok(rtc_set_time(rtc, &start_time), "Cannot set calendar");

	/*
	 * Ten RTC seconds take at most 10 * (128 * 250) / 17000 =
	 * 18.824 real seconds with the documented LSI range. The remaining
	 * 6.176 seconds are an explicit test execution/service budget, NOT
	 * a hardware-guaranteed interrupt or thread latency bound. Excessive
	 * scheduling/interrupt delay therefore fails this bounded test.
	 * Timestamping in the callback avoids confusing thread wakeup time
	 * with callback time; delivery outside the target second also fails.
	 */
	const int64_t deadline = k_uptime_get() + TEST_TIMEOUT_MS;

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						 &observations[id]),
			   "Cannot register callback %u", (unsigned int)id);
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time),
			   "Cannot arm alarm %u", (unsigned int)id);
	}

	while (received < 2) {
		int64_t remaining = deadline - k_uptime_get();

		if (remaining <= 0 ||
		    k_sem_take(&completed, K_MSEC(remaining)) != 0) {
			break;
		}
		++received;
	}

	/* Stop further events before inspecting the published observations. */
	for (uint16_t id = 0; id < 2; ++id) {
		disable_result[id] = rtc_alarm_set_time(rtc, id, 0, NULL);
		unregister_result[id] = rtc_alarm_set_callback(rtc, id, NULL, NULL);
	}

	zassert_equal(received, 2, "Both callbacks did not arrive within 25 s");
	for (uint16_t id = 0; id < 2; ++id) {
		const struct observation *o = &observations[id];

		zassert_ok(disable_result[id], "Cannot disable alarm");
		zassert_ok(unregister_result[id], "Cannot unregister callback");
		zassert_equal(atomic_get(&o->calls), 1,
			      "Expected exactly one callback per channel");
		zassert_equal(o->id, id, "Callback reported the wrong alarm ID");
		zassert_ok(o->read_result, "Callback could not read RTC time");
		zassert_true(calendar_compare(&o->time, &alarm_time) >= 0,
			     "Alarm %u callback was premature", (unsigned int)id);
		zassert_equal(calendar_compare(&o->time, &alarm_time), 0,
			      "Alarm %u callback missed the configured RTC second",
			      (unsigned int)id);
	}
}

ZTEST_SUITE(rtc_alarm_callbacks, NULL, NULL, NULL, NULL, NULL);
