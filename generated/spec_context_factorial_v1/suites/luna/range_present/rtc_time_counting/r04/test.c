#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#include <stdbool.h>
#include <stdint.h>

#define RTC_OBSERVE_INTERVAL_MS 100
#define RTC_OBSERVE_LIMIT 600 /* 60 s: > 10 s at the slowest specified LSI rate. */

static const struct rtc_time initial_time = {
	.tm_sec = 55,
	.tm_min = 59,
	.tm_hour = 23,
	.tm_mday = 31,
	.tm_mon = 11,
	.tm_year = 124, /* Years since 1900: 2024. */
};

/* Convert a valid RTC calendar value to seconds since 1970, without libc. */
static bool rtc_calendar_seconds(const struct rtc_time *t, int64_t *seconds)
{
	int year = t->tm_year + 1900;
	int month = t->tm_mon + 1;
	static const int days_in_month[] = {
		31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
	};
	int days;
	int64_t y;

	if (month < 1 || month > 12 || t->tm_mday < 1 ||
	    t->tm_hour < 0 || t->tm_hour > 23 ||
	    t->tm_min < 0 || t->tm_min > 59 ||
	    t->tm_sec < 0 || t->tm_sec > 59) {
		return false;
	}

	days = days_in_month[month - 1];
	if (month == 2 && ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)) {
		days++;
	}
	if (t->tm_mday > days) {
		return false;
	}

	y = year;
	y -= month <= 2;
	*seconds = (365 * y + y / 4 - y / 100 + y / 400) * 86400;
	for (int m = 1; m < month; m++) {
		*seconds += (int64_t)days_in_month[m - 1] * 86400;
		if (m == 2 && ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)) {
			*seconds += 86400;
		}
	}
	*seconds += (int64_t)(t->tm_mday - 1) * 86400 +
		    (int64_t)t->tm_hour * 3600 + (int64_t)t->tm_min * 60 + t->tm_sec;
	return true;
}

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time observed;
	int64_t initial_seconds;
	int64_t previous_seconds;
	bool reached_target = false;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	zassert_ok(rtc_set_time(rtc, &initial_time), "Setting initial RTC calendar failed");
	zassert_ok(rtc_get_time(rtc, &observed), "Reading initial RTC calendar failed");
	zassert_equal(observed.tm_year, initial_time.tm_year, "Initial year mismatch");
	zassert_equal(observed.tm_mon, initial_time.tm_mon, "Initial month mismatch");
	zassert_equal(observed.tm_mday, initial_time.tm_mday, "Initial day mismatch");
	zassert_equal(observed.tm_hour, initial_time.tm_hour, "Initial hour mismatch");
	zassert_equal(observed.tm_min, initial_time.tm_min, "Initial minute mismatch");
	zassert_equal(observed.tm_sec, initial_time.tm_sec, "Initial second mismatch");
	zassert_true(rtc_calendar_seconds(&observed, &initial_seconds), "Invalid initial calendar");
	previous_seconds = initial_seconds;

	/* Prescaler 128 x 250 at 17 kHz gives about 1.88 s per RTC second;
	 * ten seconds therefore take about 18.8 s at the slowest specified rate.
	 * The 60 s budget adds margin for polling and thread/interrupt delivery.
	 */
	for (int i = 0; i < RTC_OBSERVE_LIMIT; i++) {
		int64_t current_seconds;

		k_sleep(K_MSEC(RTC_OBSERVE_INTERVAL_MS));
		zassert_ok(rtc_get_time(rtc, &observed), "Reading RTC calendar failed");
		zassert_true(rtc_calendar_seconds(&observed, &current_seconds),
			     "RTC returned an invalid calendar");
		zassert_true(current_seconds >= previous_seconds,
			     "RTC calendar moved backward");
		previous_seconds = current_seconds;
		if (current_seconds >= initial_seconds + 10) {
			reached_target = true;
			break;
		}
	}
	zassert_true(reached_target, "RTC did not advance ten calendar seconds within 60 s");
	zassert_true(observed.tm_year > initial_time.tm_year ||
		     (observed.tm_year == initial_time.tm_year &&
		      (observed.tm_mon > initial_time.tm_mon ||
		       (observed.tm_mon == initial_time.tm_mon && observed.tm_mday > initial_time.tm_mday))),
		     "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
