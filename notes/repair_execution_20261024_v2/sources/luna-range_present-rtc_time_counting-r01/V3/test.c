#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

#define RTC_OBSERVATION_BOUND_SECONDS 60

static int64_t days_before_year(int year)
{
	int64_t y = year - 1;

	return 365 * y + y / 4 - y / 100 + y / 400;
}

static int64_t rtc_time_seconds(const struct rtc_time *time)
{
	static const int days_in_month[] = {
		31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
	};
	int year = time->tm_year + 1900;
	int month = time->tm_mon;
	int day_of_year = 0;

	if (month < 0 || month >= 12 || time->tm_mday < 1 ||
	    time->tm_hour < 0 || time->tm_hour > 23 || time->tm_min < 0 ||
	    time->tm_min > 59 || time->tm_sec < 0 || time->tm_sec > 59) {
		return INT64_MIN;
	}

	for (int i = 0; i < month; i++) {
		day_of_year += days_in_month[i];
	}
	if (month > 1 && (year % 4 == 0) && ((year % 100 != 0) || (year % 400 == 0))) {
		day_of_year++;
	}
	day_of_year += time->tm_mday - 1;

	return (days_before_year(year) + day_of_year) * 86400 +
	       time->tm_hour * 3600 + time->tm_min * 60 + time->tm_sec;
}

ZTEST(rtc_calendar, test_counts_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time initial = {
		.tm_sec = 50,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
	};
	struct rtc_time observed;
	int64_t initial_seconds;
	int64_t previous_seconds;
	bool reached_target = false;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_equal(rtc_set_time(rtc, &initial), 0, "RTC set failed");
	zassert_equal(rtc_get_time(rtc, &observed), 0, "Initial RTC read failed");
	zassert_equal(observed.tm_year, initial.tm_year, "Initial year mismatch");
	zassert_equal(observed.tm_mon, initial.tm_mon, "Initial month mismatch");
	zassert_equal(observed.tm_mday, initial.tm_mday, "Initial day mismatch");
	zassert_equal(observed.tm_hour, initial.tm_hour, "Initial hour mismatch");
	zassert_equal(observed.tm_min, initial.tm_min, "Initial minute mismatch");
	zassert_equal(observed.tm_sec, initial.tm_sec, "Initial second mismatch");

	initial_seconds = rtc_time_seconds(&observed);
	zassert_true(initial_seconds != INT64_MIN, "Invalid initial RTC calendar");
	previous_seconds = initial_seconds;

	/* At 17 kHz / (128 * 250), ten RTC seconds take at most about 18.9 s.
	 * A 60 s polling window leaves substantial scheduling and delivery margin.
	 */
	for (int i = 0; !repair_expired(); i++) {
		k_sleep(K_SECONDS(1));
		zassert_equal(rtc_get_time(rtc, &observed), 0, "RTC read failed");

		int64_t current_seconds = rtc_time_seconds(&observed);

		zassert_true(current_seconds != INT64_MIN, "Invalid RTC calendar");
		zassert_true(current_seconds >= previous_seconds,
			     "RTC calendar moved backward");
		previous_seconds = current_seconds;

		if (current_seconds - initial_seconds >= 10) {
			reached_target = true;
			break;
		}
	}

	zassert_true(reached_target,
		    "RTC did not advance ten calendar seconds within the observation bound");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
