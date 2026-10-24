#include <stdint.h>
#include <time.h>

#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_OBSERVATION_BOUND_MS 60000
#define RTC_POLL_INTERVAL_MS 250
#define RTC_TARGET_DELTA_SECONDS 10

static int64_t rtc_time_to_epoch(const struct rtc_time *rtc)
{
	struct tm calendar = {
		.tm_sec = rtc->tm_sec,
		.tm_min = rtc->tm_min,
		.tm_hour = rtc->tm_hour,
		.tm_mday = rtc->tm_mday,
		.tm_mon = rtc->tm_mon,
		.tm_year = rtc->tm_year,
	};

	return timeutil_timegm(&calendar);
}

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_sec = 50,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124, /* 2024 */
	};
	struct rtc_time observed;
	struct rtc_time previous;
	int64_t initial_epoch;
	int64_t previous_epoch;
	int64_t observed_epoch;
	int64_t deadline;
	int ret;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");

	ret = rtc_set_time(rtc, &initial);
	zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);
	ret = rtc_get_time(rtc, &observed);
	zassert_equal(ret, 0, "Initial rtc_get_time failed: %d", ret);

	initial_epoch = rtc_time_to_epoch(&initial);
	observed_epoch = rtc_time_to_epoch(&observed);
	zassert_equal(observed_epoch, initial_epoch,
		      "Initial RTC readback differs from set value");
	previous = observed;
	previous_epoch = observed_epoch;
	deadline = k_uptime_get() + RTC_OBSERVATION_BOUND_MS;

	/* At the documented 17 kHz LSI minimum, 10 RTC seconds take under 19 s
	 * with a 128 x 250 prescaler. The 60 s bound allows additional time for
	 * sampling and thread delivery; the oscillator specification itself does
	 * not guarantee an ISR-to-thread latency.
	 */
	while (k_uptime_get() < deadline) {
		k_sleep(K_MSEC(RTC_POLL_INTERVAL_MS));
		ret = rtc_get_time(rtc, &observed);
		zassert_equal(ret, 0, "rtc_get_time failed: %d", ret);

		observed_epoch = rtc_time_to_epoch(&observed);
		zassert_true(observed_epoch >= previous_epoch,
			     "RTC calendar moved backward");
		previous = observed;
		previous_epoch = observed_epoch;

		if (observed_epoch - initial_epoch >= RTC_TARGET_DELTA_SECONDS) {
			break;
		}
	}

	zassert_true(observed_epoch - initial_epoch >= RTC_TARGET_DELTA_SECONDS,
		     "RTC did not advance by 10 seconds within the observation bound");
	zassert_true(observed.tm_year > initial.tm_year ||
		     (observed.tm_year == initial.tm_year &&
		      (observed.tm_mon > initial.tm_mon ||
		       (observed.tm_mon == initial.tm_mon &&
			(observed.tm_mday > initial.tm_mday ||
			 (observed.tm_mday == initial.tm_mday &&
			  (observed.tm_hour > initial.tm_hour ||
			   (observed.tm_hour == initial.tm_hour &&
			    (observed.tm_min > initial.tm_min ||
			     (observed.tm_min == initial.tm_min &&
			      observed.tm_sec >= initial.tm_sec))))))))),
		     "RTC calendar did not cross the year boundary");
	zassert_equal(observed.tm_year, 125, "Expected year 2025");
	zassert_equal(observed.tm_mon, 0, "Expected January");
	zassert_equal(observed.tm_mday, 1, "Expected day 1");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
