#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define OBSERVATION_MS 30000
#define POLL_MS 100

/* Calendar seconds relative to 2026-01-01 00:00:00. */
static int32_t calendar_seconds(const struct rtc_time *t)
{
	bool before = t->tm_year == 125 && t->tm_mon == 11 &&
		      t->tm_mday == 31;
	bool after = t->tm_year == 126 && t->tm_mon == 0 &&
		     t->tm_mday == 1;

	zassert_true(before || after, "Unexpected RTC date");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24,
		     "Invalid RTC hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60,
		     "Invalid RTC minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60,
		     "Invalid RTC second");

	return (before ? -86400 : 0) + t->tm_hour * 3600 +
	       t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time initial = {
		.tm_year = 125,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,
		.tm_yday = 364,
		.tm_isdst = -1,
	};
	struct rtc_time observed;
	int32_t first, previous;
	int64_t start;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(rtc_set_time(rtc, &initial), 0,
		      "rtc_set_time failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0,
		      "Initial rtc_get_time failed");

	first = calendar_seconds(&observed);
	zassert_true(first >= -5 && first < 0,
		     "Initial calendar must precede the year boundary");
	previous = first;
	start = k_uptime_get();

	/*
	 * At the documented minimum LSI frequency, ten calendar seconds
	 * require at most 10 * (128 * 250) / 17000 = 18.824 real seconds.
	 * Use a 30-second observation budget, with 100-ms polling, leaving
	 * about 11 seconds for polling and execution delays.
	 *
	 * This is a test timeout policy, not a hardware-derived bound on
	 * ISR-to-thread latency. A late thread resumption fails the timeout;
	 * no public thread API can guarantee timely execution if scheduling
	 * is indefinitely delayed. Uptime controls only the observation
	 * budget; all progress and ordering checks compare RTC calendars.
	 */
	for (;;) {
		int32_t current;

		k_sleep(K_MSEC(POLL_MS));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "rtc_get_time failed while observing");
		zassert_true(k_uptime_get() - start <= OBSERVATION_MS,
			     "RTC observation budget expired");

		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;

		if (current - first >= 10) {
			zassert_true(current >= 0, "Year boundary was not crossed");
			break;
		}
	}
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
