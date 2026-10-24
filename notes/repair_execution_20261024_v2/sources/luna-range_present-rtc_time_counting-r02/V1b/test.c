#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

#define RTC_OBSERVATION_BOUND_MS 60000
#define RTC_POLL_INTERVAL_MS 100
#define RTC_REQUIRED_ELAPSED_SECONDS 10

static const struct rtc_time initial_time = {
	.tm_sec = 50,
	.tm_min = 59,
	.tm_hour = 23,
	.tm_mday = 31,
	.tm_mon = 11,
	.tm_year = 124, /* 2024, years since 1900 */
	.tm_wday = 2,
	.tm_yday = 365,
	.tm_isdst = -1,
};

/* Convert a Gregorian calendar value to seconds on a continuous timeline. */
static int64_t calendar_seconds(const struct rtc_time *time)
{
	int64_t year = (int64_t)time->tm_year + 1900;
	int64_t month = (int64_t)time->tm_mon + 1;
	int64_t days;

	year -= month <= 2;
	days = 365 * year + year / 4 - year / 100 + year / 400;
	days += (153 * (month + (month > 2 ? -3 : 9)) + 2) / 5;
	days += time->tm_mday - 1;

	return (((days * 24 + time->tm_hour) * 60 + time->tm_min) * 60) +
		time->tm_sec;
}

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time observed;
	struct rtc_time previous;
	int64_t initial_seconds;
	int64_t previous_seconds;
	int64_t observed_seconds;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");

	rc = rtc_set_time(rtc, &initial_time);
	zassert_equal(rc, 0, "rtc_set_time failed: %d", rc);

	rc = rtc_get_time(rtc, &observed);
	zassert_equal(rc, 0, "initial rtc_get_time failed: %d", rc);
	zassert_equal(calendar_seconds(&observed),
		      calendar_seconds(&initial_time),
		      "RTC did not read back the set calendar time");

	initial_seconds = calendar_seconds(&initial_time);
	previous = observed;
	previous_seconds = calendar_seconds(&previous);

	/*
	 * At the characterized minimum LSI rate, 10 RTC seconds take at most
	 * 10 * (128 * 250) / 17000 = 18.83 seconds. The 60-second bound
	 * leaves substantial time for polling and thread/interrupt delivery.
	 */
	for (int64_t elapsed_ms = 0; !repair_expired();
	     elapsed_ms += RTC_POLL_INTERVAL_MS) {
		k_sleep(K_MSEC(RTC_POLL_INTERVAL_MS));

		rc = rtc_get_time(rtc, &observed);
		zassert_equal(rc, 0, "rtc_get_time failed: %d", rc);

		observed_seconds = calendar_seconds(&observed);
		zassert_true(observed_seconds >= previous_seconds,
			     "RTC calendar moved backward");
		previous = observed;
		previous_seconds = observed_seconds;

		if (observed_seconds - initial_seconds >=
		    RTC_REQUIRED_ELAPSED_SECONDS) {
			zassert_true(observed.tm_year > initial_time.tm_year ||
				     (observed.tm_year == initial_time.tm_year &&
				      observed.tm_mon > initial_time.tm_mon) ||
				     (observed.tm_year == initial_time.tm_year &&
				      observed.tm_mon == initial_time.tm_mon &&
				      observed.tm_mday > initial_time.tm_mday),
				     "RTC did not cross the year boundary");
			return;
		}
	}

	zassert_true(false, "RTC did not advance by 10 seconds within %d ms",
		     RTC_OBSERVATION_BOUND_MS);
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
