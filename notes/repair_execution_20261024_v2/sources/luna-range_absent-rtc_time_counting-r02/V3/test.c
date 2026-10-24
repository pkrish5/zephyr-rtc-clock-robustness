#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

#define OBSERVATION_BOUND_MS 30000
#define POLL_INTERVAL_MS 250

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

/* Convert Gregorian calendar fields to seconds since 1970-01-01 UTC. */
static int64_t calendar_seconds(const struct rtc_time *t)
{
	int year = t->tm_year + 1900;
	unsigned int month = t->tm_mon + 1;
	int y = year - (month <= 2);
	int era = (y >= 0 ? y : y - 399) / 400;
	unsigned int yoe = y - era * 400;
	unsigned int doy = (153 * (month + (month > 2 ? -3 : 9)) + 2) / 5
			   + t->tm_mday - 1;
	unsigned int doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
	int64_t days = (int64_t)era * 146097 + doe - 719468;

	return days * 86400 + t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;
}

ZTEST(rtc_calendar, test_calendar_advances_across_year_boundary)
{
	const struct rtc_time start = {
		.tm_sec = 50,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124, /* 2024 */
	};
	struct rtc_time observed;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "Could not set RTC calendar");
	zassert_ok(rtc_get_time(rtc, &observed), "Could not read initial RTC calendar");

	int64_t initial = calendar_seconds(&start);
	int64_t previous = calendar_seconds(&observed);

	zassert_true(previous >= initial && previous <= initial + 1,
		     "Initial RTC read does not match set time: %lld vs %lld",
		     (long long)previous, (long long)initial);

	int elapsed_ms = 0;
	while (!repair_expired() && previous < initial + 10) {
		k_sleep(K_MSEC(POLL_INTERVAL_MS));
		elapsed_ms += POLL_INTERVAL_MS;
		zassert_ok(rtc_get_time(rtc, &observed), "Could not read RTC calendar");
		int64_t current = calendar_seconds(&observed);

		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
	}

	zassert_true(previous >= initial + 10,
		     "RTC did not advance ten calendar seconds within %d ms",
		     OBSERVATION_BOUND_MS);
	zassert_true(observed.tm_year > start.tm_year ||
		     (observed.tm_year == start.tm_year && observed.tm_mon >= start.tm_mon),
		     "RTC year/month fields regressed");
	zassert_true(observed.tm_year > start.tm_year || observed.tm_mon == 0,
		     "RTC did not cross into the new year");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
