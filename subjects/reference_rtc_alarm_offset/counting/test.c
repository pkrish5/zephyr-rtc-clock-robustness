#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>
#include <time.h>
#include "../reference_common.h"

static const struct device *const rtc_dev = DEVICE_DT_GET(DT_ALIAS(rtc));

static int64_t calendar_seconds(const struct rtc_time *t)
{
	return (int64_t)timeutil_timegm((const struct tm *)t);
}

ZTEST(reference_rtc, test_calendar_counting)
{
	struct rtc_time now;
	int64_t previous = calendar_seconds(&reference_start);
	uint32_t start_ms;

	zassert_true(device_is_ready(rtc_dev), "RTC not ready");
	start_ms = k_uptime_get_32();
	zassert_ok(rtc_set_time(rtc_dev, &reference_start), "set time");
	for (;;) {
		uint32_t elapsed = k_uptime_get_32() - start_ms;
		int64_t current;
		zassert_ok(rtc_get_time(rtc_dev, &now), "read time");
		current = calendar_seconds(&now);
		zassert_true(current >= previous, "calendar went backwards");
		if (current >= calendar_seconds(&reference_target)) {
			zassert_true(elapsed >= REFERENCE_EARLIEST_MS,
				     "calendar reached target too early");
			zassert_true(reference_crossed_midnight(&now), "midnight not crossed");
			break;
		}
		zassert_true(elapsed <= REFERENCE_CEILING_MS,
			     "calendar did not reach target by ceiling");
		previous = current;
		k_msleep(REFERENCE_POLL_MS);
	}
}

ZTEST_SUITE(reference_rtc, NULL, NULL, NULL, NULL, NULL);
