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
#define OBSERVATION_MS 30000

BUILD_ASSERT(ALARM_MASK == 7U);

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static const struct rtc_time initial = {
	.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
};

static const struct rtc_time target = {
	.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
};

static bool before_target(const struct rtc_time *t)
{
	const int actual[] = {
		t->tm_year, t->tm_mon, t->tm_mday,
		t->tm_hour, t->tm_min, t->tm_sec,
	};
	const int expected[] = {125, 0, 1, 0, 0, 5};

	for (unsigned int i = 0; i < ARRAY_SIZE(actual); ++i) {
		if (actual[i] != expected[i]) {
			return actual[i] < expected[i];
		}
	}
	return false;
}

ZTEST(rtc_alarm_pending, test_year_rollover)
{
	struct rtc_time readback = {0};
	struct rtc_time now = {0};
	uint16_t mask = 0;
	bool saw_early_clear = false;
	bool saw_pending = false;
	bool premature = false;
	int pending_rc = 0;
	int time_rc = 0;
	int disable_rc;

	zassert_true(device_is_ready(rtc), "RTC is not ready");

	/* Quiesce both board alarm channels and consume old pending state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0);
	}

	zassert_ok(rtc_set_time(rtc, &initial));
	zassert_ok(rtc_alarm_set_time(rtc, ALARM_ID, ALARM_MASK, &target));
	zassert_ok(rtc_alarm_get_time(rtc, ALARM_ID, &mask, &readback));
	zassert_equal(mask, ALARM_MASK);
	zassert_equal(readback.tm_sec, target.tm_sec);
	zassert_equal(readback.tm_min, target.tm_min);
	zassert_equal(readback.tm_hour, target.tm_hour);
	/* Date fields are deliberately excluded from this hardware alarm mask. */

	/*
	 * Ten RTC seconds take at most 10 * 32000 / 17000 = 18.824 s.
	 * Allowing two additional calendar ticks gives 22.589 s. The 30 s
	 * polling budget includes a separate responsiveness allowance; the
	 * oscillator specification does NOT guarantee interrupt latency.
	 *
	 * On this single CPU, keep this thread runnable with scheduling
	 * locked and interrupts enabled. The driver's alarm ISR can execute
	 * without requiring another thread to be scheduled. No callback or
	 * semaphore delivery is involved. As with any on-board timeout,
	 * this bounds observation while the CPU executes, not an interrupt
	 * handler that never returns or an indefinitely halted processor.
	 */
	k_sched_lock();
	const int64_t deadline = k_uptime_get() + OBSERVATION_MS;

	for (;;) {
		/* is_pending may consume the indication: retain every result. */
		pending_rc = rtc_alarm_is_pending(rtc, ALARM_ID);
		time_rc = rtc_get_time(rtc, &now);
		if (pending_rc < 0 || time_rc != 0) {
			break;
		}

		/*
		 * Sample the calendar AFTER pending. If it is still early,
		 * that pending indication was necessarily premature. Reading
		 * the calendar first would introduce a rollover race.
		 */
		if (before_target(&now)) {
			if (pending_rc != 0) {
				premature = true;
				break;
			}
			saw_early_clear = true;
		} else if (pending_rc != 0) {
			saw_pending = true;
			break;
		}

		if (k_uptime_get() >= deadline) {
			break;
		}
		k_busy_wait(1000);
	}
	k_sched_unlock();

	disable_rc = rtc_alarm_set_time(rtc, ALARM_ID, 0, NULL);
	zassert_true(pending_rc >= 0, "Pending query failed: %d", pending_rc);
	zassert_ok(time_rc, "Calendar read failed");
	zassert_false(premature, "Alarm pending before configured RTC time");
	zassert_true(saw_early_clear, "No pre-alarm clear state observed");
	zassert_false(before_target(&now), "RTC did not reach target within budget");
	zassert_true(saw_pending, "No pending alarm within observation budget");
	zassert_ok(disable_rc, "Alarm cleanup failed");
}

ZTEST_SUITE(rtc_alarm_pending, NULL, NULL, NULL, NULL, NULL);
