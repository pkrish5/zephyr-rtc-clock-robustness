#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVATION_BOUND_SECONDS 20

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));

static int64_t calendar_seconds(const struct rtc_time *time)
{
	struct tm calendar = {
		.tm_sec = time->tm_sec,
		.tm_min = time->tm_min,
		.tm_hour = time->tm_hour,
		.tm_mday = time->tm_mday,
		.tm_mon = time->tm_mon,
		.tm_year = time->tm_year,
	};

	return (int64_t)timeutil_timegm(&calendar);
}

ZTEST(rtc_calendar, test_calendar_advances_across_year_boundary)
{
	zassert_true(device_is_ready(rtc), "RTC device is not ready");

	/* rtc_time uses years since 1900 and months in the range 0..11. */
	struct rtc_time initial = {
		.tm_sec = 50,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124, /* 2024 */
	};
	zassert_equal(rtc_set_time(rtc, &initial), 0, "RTC calendar set failed");

	struct rtc_time observed;
	zassert_equal(rtc_get_time(rtc, &observed), 0, "Initial RTC read failed");
	int64_t initial_seconds = calendar_seconds(&initial);
	int64_t previous_seconds = calendar_seconds(&observed);
	zassert_equal(previous_seconds, initial_seconds,
		      "RTC did not retain the initial calendar value");

	int64_t target_seconds = initial_seconds + 10;
	int64_t deadline_ms = k_uptime_get() +
		((RTC_OBSERVATION_BOUND_SECONDS + 2) * MSEC_PER_SEC);
	bool reached_target = false;

	while (k_uptime_get() < deadline_ms) {
		k_sleep(K_MSEC(200));
		zassert_equal(rtc_get_time(rtc, &observed), 0,
			      "RTC calendar read failed");

		int64_t current_seconds = calendar_seconds(&observed);
		zassert_true(current_seconds >= previous_seconds,
			     "RTC calendar moved backward");
		previous_seconds = current_seconds;

		if (current_seconds >= target_seconds) {
			reached_target = true;
			break;
		}
	}

	zassert_true(reached_target,
		    "RTC did not advance ten calendar seconds within the observation bound");
	zassert_true(previous_seconds >= target_seconds,
		    "RTC calendar did not reach the ten-second target");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
