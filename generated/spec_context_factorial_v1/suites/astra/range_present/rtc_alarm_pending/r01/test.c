#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define ALARM_ID 0U
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define OBSERVATION_MS 25000

BUILD_ASSERT(ALARM_MASK == 7, "Expected second/minute/hour mask");

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static const struct rtc_time start_time = {
	.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	.tm_nsec = 0,
};

static const struct rtc_time alarm_time = {
	.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	.tm_nsec = 0,
};

/* Compare calendar fields, including the year rollover. */
static int calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
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

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	struct rtc_time readback = {0};
	struct rtc_time before, after;
	uint16_t mask = 0;
	bool checked_early = false;
	bool reached_target = false;
	bool observed_pending = false;
	int pending;

	zassert_true(device_is_ready(rtc), "RTC is not ready");

	/* Disable both hardware channels and consume existing pending state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_equal(rtc_alarm_set_time(rtc, id, 0, NULL), 0,
			      "Cannot disable alarm %u", (unsigned int)id);
		pending = rtc_alarm_is_pending(rtc, id);
		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
	}

	zassert_equal(rtc_set_time(rtc, &start_time), 0,
		      "Cannot set calendar");
	const int64_t deadline = k_uptime_get() + OBSERVATION_MS;

	/* Only time-of-day fields participate in the hardware comparison. */
	zassert_equal(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK,
					 &alarm_time), 0,
		      "Cannot configure alarm");
	zassert_equal(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback),
		      0, "Cannot read alarm");
	zassert_equal(mask, ALARM_MASK, "Alarm mask differs");
	zassert_equal(readback.tm_sec, alarm_time.tm_sec, "Second differs");
	zassert_equal(readback.tm_min, alarm_time.tm_min, "Minute differs");
	zassert_equal(readback.tm_hour, alarm_time.tm_hour, "Hour differs");

	/*
	 * At the slowest characterized LSI rate, one calendar second takes
	 * 32000/17000 wall seconds. Allowing eleven ticks for the ten-second
	 * interval and phase uncertainty requires less than 20.71 seconds.
	 * The 25-second deadline adds over four seconds of execution and
	 * interrupt-service allowance. This is an explicit test budget, not
	 * an ISR-to-thread latency guarantee derived from the LSI bounds.
	 * Sleeping lets interrupt handling and other runnable work progress.
	 */
	while (k_uptime_get() < deadline) {
		zassert_equal(rtc_get_time(rtc, &before), 0,
			      "Cannot read calendar before pending query");
		pending = rtc_alarm_is_pending(rtc, ALARM_ID);
		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
		zassert_equal(rtc_get_time(rtc, &after), 0,
			      "Cannot read calendar after pending query");
		zassert_true(calendar_cmp(&after, &before) >= 0,
			     "Calendar moved backwards");

		/* Bracket the query to avoid a false failure at the boundary. */
		if (calendar_cmp(&after, &alarm_time) < 0) {
			zassert_equal(pending, 0, "Alarm became pending early");
			checked_early = true;
		} else {
			reached_target = true;
		}

		if (pending == 1) {
			/* The pending query consumes the indication; retain it. */
			observed_pending = true;
			break;
		}
		k_sleep(K_MSEC(10));
	}

	zassert_equal(rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL), 0,
		      "Cannot disable tested alarm");
	zassert_true(checked_early, "No pre-target observation was obtained");
	zassert_true(reached_target, "RTC did not reach target within 25 s");
	zassert_true(observed_pending,
		     "Alarm pending was not delivered within the 25 s test budget");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
