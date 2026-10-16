#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include "../reference_common.h"

static const struct device *const rtc_dev = DEVICE_DT_GET(DT_ALIAS(rtc));
static K_SEM_DEFINE(callback_event, 0, 2);
static atomic_t count[2];
static atomic_t bad_id;
static atomic_t early;
static uint32_t start_ms;

static void reference_callback(const struct device *dev, uint16_t id, void *user_data)
{
	struct rtc_time at_callback;
	uint32_t elapsed = k_uptime_get_32() - start_ms;

	if (dev != rtc_dev || id >= 2 || id != (uintptr_t)user_data) {
		atomic_set(&bad_id, 1);
	} else {
		atomic_inc(&count[id]);
	}
	if (elapsed < REFERENCE_EARLIEST_MS ||
	    rtc_get_time(dev, &at_callback) != 0 ||
	    !reference_at_target(&at_callback)) {
		atomic_set(&early, 1);
	}
	k_sem_give(&callback_event);
}

ZTEST(reference_rtc, test_alarm_callback)
{
	struct rtc_time now;
	uint32_t elapsed;

	zassert_true(device_is_ready(rtc_dev), "RTC not ready");
	for (int id = 0; id < 2; ++id) {
		atomic_set(&count[id], 0);
		zassert_ok(rtc_alarm_set_time(rtc_dev, id, 0, NULL), "clear alarm");
		zassert_ok(rtc_alarm_set_callback(rtc_dev, id, NULL, NULL), "clear callback");
	}
	atomic_set(&bad_id, 0);
	atomic_set(&early, 0);
	k_sem_reset(&callback_event);
	start_ms = k_uptime_get_32();
	zassert_ok(rtc_set_time(rtc_dev, &reference_start), "set time");
	for (int id = 0; id < 2; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc_dev, id, REFERENCE_ALARM_MASK,
					      &reference_target), "set alarm");
		struct rtc_time programmed;
		uint16_t programmed_mask;
		zassert_ok(rtc_alarm_get_time(rtc_dev, id, &programmed_mask,
					      &programmed), "read programmed alarm");
		zassert_equal(programmed.tm_sec, reference_target.tm_sec,
			      "programmed alarm second differs from requested target");
		zassert_equal(programmed.tm_min, reference_target.tm_min,
			      "programmed alarm minute differs from requested target");
		zassert_equal(programmed.tm_hour, reference_target.tm_hour,
			      "programmed alarm hour differs from requested target");
		zassert_ok(rtc_alarm_set_callback(rtc_dev, id, reference_callback,
						 (void *)(uintptr_t)id), "set callback");
	}
	for (;;) {
		elapsed = k_uptime_get_32() - start_ms;
		zassert_equal(atomic_get(&early), 0, "alarm fired early");
		zassert_equal(atomic_get(&bad_id), 0, "wrong alarm id");
		if (atomic_get(&count[0]) && atomic_get(&count[1])) {
			break;
		}
		zassert_true(elapsed <= REFERENCE_CEILING_MS,
			     "callbacks absent past legal-clock ceiling plus service margin");
		(void)k_sem_take(&callback_event, K_MSEC(REFERENCE_POLL_MS));
	}
	zassert_ok(rtc_get_time(rtc_dev, &now), "read calendar");
	zassert_true(reference_at_target(&now), "callback before calendar target");
	zassert_equal(atomic_get(&count[0]), 1, "alarm 0 count");
	zassert_equal(atomic_get(&count[1]), 1, "alarm 1 count");
}

ZTEST_SUITE(reference_rtc, NULL, NULL, NULL, NULL, NULL);
