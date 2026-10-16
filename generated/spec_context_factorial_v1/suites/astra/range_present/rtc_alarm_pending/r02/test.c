#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define POLL_MS 10
/*
 * Ten calendar seconds take at most 10 * 32000 / 17000 seconds.
 * Allow one additional calendar tick for phase/setup uncertainty: 20706 ms.
 * The additional 2000 ms is an explicit test service-latency budget (200
 * polling intervals), NOT an ISR-delivery guarantee derived from the LSI
 * specification. A timeout fails this observation budget; it does not by
 * itself identify an oscillator, interrupt, or driver fault.
 */
#define CLOCK_BUDGET_MS ((11LL * 32000 * 1000 + 16999) / 17000)
#define SERVICE_BUDGET_MS 2000

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

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

/* Compare calendar fields, including the year rollover; ignore subseconds. */
static bool before_target(const struct rtc_time *t)
{
	const int actual[] = { t->tm_year, t->tm_mon, t->tm_mday,
			       t->tm_hour, t->tm_min, t->tm_sec };
	const int expected[] = { 125, 0, 1, 0, 0, 5 };

	for (unsigned int i = 0; i < ARRAY_SIZE(actual); ++i) {
		if (actual[i] != expected[i]) {
			return actual[i] < expected[i];
		}
	}
	return false;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	struct rtc_time readback;
	uint16_t mask;
	bool observed_before = false;
	bool observed_pending = false;
	bool reached_target = false;
	int pending;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	/* Disable both hardware channels and consume any old pending state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		pending = rtc_alarm_is_pending(rtc, id);
		zassert_true(pending == 0 || pending == 1,
			     "Pending read failed: %d", pending);
	}

	zassert_ok(rtc_set_time(rtc, &start));
	const int64_t deadline = k_uptime_get() + CLOCK_BUDGET_MS +
				 SERVICE_BUDGET_MS;

	zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &target));
	zassert_ok(rtc_alarm_get_time(rtc, 0, &mask, &readback));
	zassert_equal(mask, ALARM_MASK);
	zassert_equal(readback.tm_sec, target.tm_sec);
	zassert_equal(readback.tm_min, target.tm_min);
	zassert_equal(readback.tm_hour, target.tm_hour);
	/* Date fields are deliberately not part of the hardware alarm mask. */

	while (k_uptime_get() < deadline) {
		pending = rtc_alarm_is_pending(rtc, 0);
		zassert_true(pending == 0 || pending == 1,
			     "Pending read failed: %d", pending);
		/*
		 * Read the calendar AFTER consuming pending. This avoids falsely
		 * reporting an early alarm when the RTC ticks between API calls.
		 */
		zassert_ok(rtc_get_time(rtc, &readback));
		zassert_true(k_uptime_get() <= deadline,
			     "Observation exceeded the test service budget");

		if (before_target(&readback)) {
			zassert_equal(pending, 0, "Alarm pending before target");
			observed_before = true;
		} else {
			reached_target = true;
			if (pending == 1) {
				observed_pending = true;
				break;
			}
		}
		k_msleep(POLL_MS);
	}

	zassert_ok(rtc_alarm_set_time(rtc, 0, 0, NULL));
	zassert_true(observed_before, "No pre-target observation was made");
	zassert_true(reached_target, "RTC did not reach target within budget");
	zassert_true(observed_pending,
		     "Alarm was not pending within the finite observation budget");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
