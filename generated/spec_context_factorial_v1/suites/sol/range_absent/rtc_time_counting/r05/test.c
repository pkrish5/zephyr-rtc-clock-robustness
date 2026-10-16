#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

/* Seconds since 2023-12-31 23:59:55; -1 means an unexpected date. */
static int calendar_offset(const struct rtc_time *t)
{
	if (t->tm_hour < 0 || t->tm_hour > 23 ||
	    t->tm_min < 0 || t->tm_min > 59 ||
	    t->tm_sec < 0 || t->tm_sec > 59) {
		return -1;
	}

	int seconds = t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;

	if (t->tm_year == 123 && t->tm_mon == 11 && t->tm_mday == 31) {
		return seconds - (23 * 3600 + 59 * 60 + 55);
	}
	if (t->tm_year == 124 && t->tm_mon == 0 && t->tm_mday == 1) {
		return seconds + 5;
	}
	return -1;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 123, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 0,
	};
	struct rtc_time observed;
	int elapsed;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &initial), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0, "Initial RTC read failed");
	elapsed = calendar_offset(&observed);
	zassert_true(elapsed >= 0 && elapsed <= 2, "Initial calendar differs from set time");

	/* 300 samples spaced 100 ms apart allow 30 CPU seconds for 10 RTC seconds. */
	for (int i = 0; i < 300 && elapsed < 10; ++i) {
		k_sleep(K_MSEC(100));
		zassert_equal(rtc_get_time(rtc, &observed), 0, "RTC read failed");
		int next = calendar_offset(&observed);

		zassert_true(next >= elapsed, "RTC calendar moved backward");
		elapsed = next;
	}

	zassert_true(elapsed >= 10, "RTC did not advance ten calendar seconds");
	zassert_equal(observed.tm_year, 124, "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
