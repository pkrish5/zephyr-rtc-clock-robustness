#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_COUNT 2
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

/* Allow 40 wall-clock seconds for 10 RTC seconds, including LSI variation
 * and scheduling overhead. All waits share this single deadline.
 */
#define TIMEOUT_MS 40000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static K_SEM_DEFINE(events, 0, ALARM_COUNT);

struct observation {
	atomic_t calls;
	uint16_t id;
	int time_result;
	struct rtc_time time;
};

static struct observation observed[ALARM_COUNT];

static const struct rtc_time start = {
	.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
};

static const struct rtc_time target = {
	.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
};

static int calendar_compare(const struct rtc_time *a,
			    const struct rtc_time *b)
{
	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday,
			  a->tm_hour, a->tm_min, a->tm_sec};
	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday,
			  b->tm_hour, b->tm_min, b->tm_sec};

	for (int i = 0; i < 6; ++i) {
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

	if (atomic_get(&o->calls) == 0) {
		o->id = id;
		/* STM32's RTC calendar read is synchronous and nonblocking.
		 * Capture the RTC time in the callback, not after a thread wakes.
		 */
		o->time_result = rtc_get_time(dev, &o->time);
		atomic_inc(&o->calls);
		k_sem_give(&events);
	} else {
		atomic_inc(&o->calls);
	}
}

ZTEST(rtc_alarm, test_year_rollover)
{
	struct rtc_time now;
	int received = 0;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t i = 0; i < ALARM_COUNT; ++i) {
		uint16_t supported = 0;

		zassert_ok(rtc_alarm_set_time(rtc, i, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, i, NULL, NULL));
		zassert_true(rtc_alarm_is_pending(rtc, i) >= 0);
		zassert_ok(rtc_alarm_get_supported_fields(rtc, i, &supported));
		zassert_equal(supported & ALARM_MASK, ALARM_MASK);
		observed[i] = (struct observation){0};
	}
	k_sem_reset(&events);

	zassert_ok(rtc_set_time(rtc, &start));
	for (uint16_t i = 0; i < ALARM_COUNT; ++i) {
		zassert_ok(rtc_alarm_set_callback(rtc, i, alarm_callback,
						&observed[i]));
		zassert_ok(rtc_alarm_set_time(rtc, i, ALARM_MASK, &target));
	}

	zassert_ok(rtc_get_time(rtc, &now));
	zassert_true(calendar_compare(&now, &target) < 0,
		     "Setup consumed the alarm lead time");

	const int64_t deadline = k_uptime_get() + TIMEOUT_MS;

	while (received < ALARM_COUNT) {
		int64_t remaining = deadline - k_uptime_get();

		if (remaining <= 0 ||
		    k_sem_take(&events, K_MSEC(remaining)) != 0) {
			break;
		}
		++received;
	}

	/* Stop delivery before examining the final observations. */
	for (uint16_t i = 0; i < ALARM_COUNT; ++i) {
		zassert_ok(rtc_alarm_set_time(rtc, i, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, i, NULL, NULL));
	}

	zassert_equal(received, ALARM_COUNT, "Missing alarm callback");
	for (uint16_t i = 0; i < ALARM_COUNT; ++i) {
		const struct observation *o = &observed[i];

		zassert_equal(atomic_get(&o->calls), 1,
			      "Alarm %u callback count", (unsigned int)i);
		zassert_equal(o->id, i, "Incorrect callback alarm ID");
		zassert_ok(o->time_result, "Callback RTC read failed");
		/* The first callback is timestamped, and duplicates fail above:
		 * an early callback cannot be hidden by a later valid callback.
		 */
		zassert_true(calendar_compare(&o->time, &target) >= 0,
			     "Alarm %u fired prematurely", (unsigned int)i);
		zassert_equal(calendar_compare(&o->time, &target), 0,
			      "Alarm %u fired outside the target RTC second",
			      (unsigned int)i);
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
