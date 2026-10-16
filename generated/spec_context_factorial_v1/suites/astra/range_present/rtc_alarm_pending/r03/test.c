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

/*
 * Ten calendar ticks take at most 10 * 32000 / 17000 seconds.
 * Round eleven ticks upward to 21 seconds, allowing another observation.
 * This bounds calendar progress, not interrupt delivery. An additional
 * explicit two-second response budget is a test acceptance criterion;
 * it is not a latency guarantee derived from the oscillator specification.
 * Busy polling with scheduling locked avoids a sleeping thread's wake-up
 * latency. Interrupts remain enabled so the RTC ISR can publish pending.
 */
#define OBSERVATION_MS 23000

static const struct rtc_time initial = {
	.tm_year = 2024 - 1900, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	.tm_nsec = 0,
};

static const struct rtc_time target = {
	.tm_year = 2025 - 1900, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	.tm_nsec = 0,
};

static bool before_target(const struct rtc_time *t)
{
	const int actual[] = {
		t->tm_year, t->tm_mon, t->tm_mday,
		t->tm_hour, t->tm_min, t->tm_sec,
	};
	const int expected[] = {125, 0, 1, 0, 0, 5};

	for (unsigned int i = 0; i < sizeof(actual) / sizeof(actual[0]); ++i) {
		if (actual[i] != expected[i]) {
			return actual[i] < expected[i];
		}
	}
	return false;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time readback = {0};
	struct rtc_time now = {0};
	uint16_t supported = 0;
	uint16_t mask = 0;
	bool saw_before = false;
	bool early = false;
	bool observed = false;
	int error = 0;
	int pending;
	int cleanup;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm field mask");
	zassert_ok(rtc_alarm_get_supported_fields(rtc, ALARM_ID, &supported));
	zassert_equal(supported & ALARM_MASK, ALARM_MASK);

	/* Disable both channels and consume any previously latched events. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		pending = rtc_alarm_is_pending(rtc, id);
		zassert_true(pending == 0 || pending == 1,
			     "Pending query failed: %d", pending);
	}

	int64_t deadline = k_uptime_get() + OBSERVATION_MS;

	zassert_ok(rtc_set_time(rtc, &initial));
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &target));
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
	zassert_equal(mask, ALARM_MASK);
	/* Dates are intentionally excluded from this hardware alarm mask. */
	zassert_equal(readback.tm_sec, target.tm_sec);
	zassert_equal(readback.tm_min, target.tm_min);
	zassert_equal(readback.tm_hour, target.tm_hour);

	k_sched_lock();
	while (k_uptime_get() < deadline) {
		pending = rtc_alarm_is_pending(rtc, ALARM_ID);
		if (pending != 0 && pending != 1) {
			error = pending;
			break;
		}

		/*
		 * Read the calendar AFTER the destructive pending query. Reading
		 * it first could misclassify a legitimate intervening alarm as
		 * early. A sample crossing the target boundary is not early
		 * evidence, and does not count as a pre-target observation.
		 */
		error = rtc_get_time(rtc, &now);
		if (error != 0) {
			break;
		}
		if (before_target(&now)) {
			saw_before = true;
			if (pending == 1) {
				early = true;
				break;
			}
		} else if (pending == 1) {
			observed = true;
			break;
		}
		k_busy_wait(1000);
	}
	k_sched_unlock();

	cleanup = rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL);
	zassert_ok(error, "RTC polling failed: %d", error);
	zassert_false(early, "Alarm pending before configured calendar time");
	zassert_true(saw_before, "No pre-target observation was obtained");
	zassert_true(observed, "Alarm not observed within %d ms", OBSERVATION_MS);
	zassert_ok(cleanup, "Failed to disable alarm");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
