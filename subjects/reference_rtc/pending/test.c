#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include "../reference_common.h"

static const struct device *const rtc_dev = DEVICE_DT_GET(DT_ALIAS(rtc));

ZTEST(reference_rtc, test_alarm_pending)
{
	struct rtc_time now;
	uint32_t start_ms;
	int pending;

	zassert_true(device_is_ready(rtc_dev), "RTC not ready");
	zassert_ok(rtc_alarm_set_callback(rtc_dev, 0, NULL, NULL), "disable callback");
	zassert_ok(rtc_alarm_set_time(rtc_dev, 0, 0, NULL), "clear alarm");
	(void)rtc_alarm_is_pending(rtc_dev, 0);
	start_ms = k_uptime_get_32();
	zassert_ok(rtc_set_time(rtc_dev, &reference_start), "set time");
	zassert_ok(rtc_alarm_set_time(rtc_dev, 0, REFERENCE_ALARM_MASK,
				      &reference_target), "set alarm");
	for (;;) {
		uint32_t elapsed = k_uptime_get_32() - start_ms;
		pending = rtc_alarm_is_pending(rtc_dev, 0);
		zassert_true(pending >= 0, "read pending");
		zassert_ok(rtc_get_time(rtc_dev, &now), "read calendar");
		if (pending == 1) {
			zassert_true(elapsed >= REFERENCE_EARLIEST_MS,
				     "pending before fastest legal transition");
			zassert_true(reference_at_target(&now), "pending before calendar target");
			break;
		}
		zassert_true(elapsed <= REFERENCE_CEILING_MS,
			     "pending absent past legal-clock ceiling plus service margin");
		k_msleep(REFERENCE_POLL_MS);
	}
}

ZTEST_SUITE(reference_rtc, NULL, NULL, NULL, NULL, NULL);
