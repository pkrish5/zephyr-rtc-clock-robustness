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

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static const uint16_t expected_ids[2] = { 0, 1 };
static atomic_t calls[2];
static atomic_t seen;
static atomic_t errors;
K_SEM_DEFINE(events, 0, 4);

static const struct rtc_time start = {
	.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
	.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
	.tm_nsec = 0,
};

static const struct rtc_time target = {
	.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
	.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
	.tm_nsec = 0,
};

/* Compare calendar fields, without depending on libc timezone handling. */
static int compare_time(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
			   a->tm_hour, a->tm_min, a->tm_sec };
	const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
			   b->tm_hour, b->tm_min, b->tm_sec };

	for (unsigned int i = 0; i < 6; ++i) {
		if (av[i] != bv[i]) {
			return av[i] < bv[i] ? -1 : 1;
		}
	}
	return 0;
}

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	const uint16_t expected = *(const uint16_t *)user_data;
	struct rtc_time now;

	/* The STM32 RTC calendar read uses hardware registers and does not
	 * block. Sample here so thread wake-up latency cannot hide an early
	 * callback or make an on-time callback appear late.
	 */
	int rc = rtc_get_time(dev, &now);

	if (dev != rtc || id != expected) {
		atomic_or(&errors, 1);
	}
	if (rc != 0) {
		atomic_or(&errors, 2);
	} else if (compare_time(&now, &target) < 0) {
		atomic_or(&errors, 4); /* Premature callback. */
	} else if (compare_time(&now, &target) > 0) {
		atomic_or(&errors, 8); /* Callback outside target second. */
	}
	atomic_inc(&calls[expected]);
	atomic_or(&seen, 1U << expected);
	k_sem_give(&events);
}

ZTEST(stm32_rtc_alarm, test_new_year_alarms)
{
	struct rtc_time now;
	int read_rc = 0;
	bool premature = false;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	for (uint16_t id = 0; id < 2; ++id) {
		uint16_t supported;

		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0);
		zassert_ok(rtc_alarm_get_supported_fields(rtc, id, &supported));
		zassert_equal(supported & ALARM_MASK, ALARM_MASK);
		atomic_clear(&calls[id]);
	}
	atomic_clear(&seen);
	atomic_clear(&errors);
	k_sem_reset(&events);

	zassert_ok(rtc_set_time(rtc, &start));

	/* Ten calendar seconds take at most 10 * 32000 / 17000 =
	 * 18.824 wall seconds. Allow 20 seconds for calendar advancement
	 * and an additional 10 seconds as an explicit test delivery budget.
	 * This is a finite acceptance timeout, not an ISR/thread latency
	 * guarantee derived from the LSI specification. Callback timestamps
	 * must still lie within the configured RTC second.
	 */
	const int64_t deadline = k_uptime_get() + 30000;

	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						(void *)&expected_ids[id]));
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &target));
	}

	while (k_uptime_get() < deadline) {
		/* Read published events before sampling the calendar, avoiding
		 * falsely labelling a callback after the sample as premature.
		 */
		atomic_val_t observed = atomic_get(&seen);

		read_rc = rtc_get_time(rtc, &now);
		if (read_rc != 0) {
			break;
		}
		if (compare_time(&now, &target) < 0 && observed != 0) {
			premature = true;
		}
		if (observed == 3) {
			break;
		}
		(void)k_sem_take(&events, K_MSEC(20));
	}

	/* Stop hardware delivery before inspecting final protected state. */
	for (uint16_t id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL));
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL));
	}

	zassert_ok(read_rc, "Calendar read failed");
	zassert_false(premature, "Callback observed before alarm time");
	zassert_equal(atomic_get(&errors), 0,
		      "Wrong device/ID, read failure, early or late callback: %ld",
		      (long)atomic_get(&errors));
	zassert_equal(atomic_get(&seen), 3, "Both alarms must arrive within 30 s");
	zassert_equal(atomic_get(&calls[0]), 1, "Alarm 0 callback count");
	zassert_equal(atomic_get(&calls[1]), 1, "Alarm 1 callback count");
}

ZTEST_SUITE(stm32_rtc_alarm, NULL, NULL, NULL, NULL, NULL);
