#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define POLL_MS 250
#define MAX_POLLS 160

/* Calendar seconds relative to 2025-12-31 23:59:55. */
static int calendar_seconds(const struct rtc_time *t)
{
	bool dec31 = t->tm_year == 125 && t->tm_mon == 11 &&
		     t->tm_mday == 31;
	bool jan1 = t->tm_year == 126 && t->tm_mon == 0 &&
		    t->tm_mday == 1;

	zassert_true(dec31 || jan1, "Unexpected calendar date");
	zassert_true(t->tm_hour >= 0 && t->tm_hour < 24,
		     "Invalid hour");
	zassert_true(t->tm_min >= 0 && t->tm_min < 60,
		     "Invalid minute");
	zassert_true(t->tm_sec >= 0 && t->tm_sec < 60,
		     "Invalid second");

	int seconds = t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;

	return jan1 ? seconds + 5 : seconds - 86395;
}

ZTEST(rtc_calendar, test_year_rollover)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 125,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 3,
		.tm_yday = 364,
		.tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time observed;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	rc = rtc_set_time(rtc, &initial);
	zassert_equal(rc, 0, "rtc_set_time failed: %d", rc);
	rc = rtc_get_time(rtc, &observed);
	zassert_equal(rc, 0, "Initial rtc_get_time failed: %d", rc);

	int first = calendar_seconds(&observed);
	int previous = first;
	bool reached = false;

	zassert_true(first >= 0 && first < 5,
		     "Initial read must match the seeded date before rollover");

	/*
	 * At most 40 seconds of requested sleep. The independent LSI is
	 * nominally 32 kHz but can be as slow as approximately 17 kHz on
	 * STM32F407. Ten RTC seconds can therefore take about 19 real
	 * seconds; 40 seconds provides ample oscillator and polling margin.
	 * Sleep only bounds observation; elapsed time is measured from the
	 * RTC calendar itself. Repeated equal readings are allowed.
	 */
	for (int i = 0; i < MAX_POLLS; ++i) {
		k_sleep(K_MSEC(POLL_MS));
		rc = rtc_get_time(rtc, &observed);
		zassert_equal(rc, 0, "rtc_get_time failed: %d", rc);

		int current = calendar_seconds(&observed);

		zassert_true(current >= previous,
			     "RTC moved backward: %d -> %d", previous, current);
		previous = current;
		if (current - first >= 10) {
			reached = true;
			break;
		}
	}

	zassert_true(reached, "RTC failed to advance ten calendar seconds");
	zassert_equal(observed.tm_year, 126, "Year did not roll over");
	zassert_equal(observed.tm_mon, 0, "Month did not roll over");
	zassert_equal(observed.tm_mday, 1, "Day did not roll over");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
