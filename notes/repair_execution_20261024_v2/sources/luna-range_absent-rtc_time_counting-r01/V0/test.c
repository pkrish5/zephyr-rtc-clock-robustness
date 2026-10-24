#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define RTC_DEVICE DEVICE_DT_GET(DT_ALIAS(rtc))
#define OBSERVATION_LIMIT_SECONDS 20
#define POLL_INTERVAL_MS 100
#define INITIAL_EPOCH_SECONDS 1893455995LL /* 2029-12-31 23:59:55 UTC */

static int64_t rtc_epoch_seconds(const struct rtc_time *time)
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

ZTEST(rtc_calendar, test_calendar_counts_across_year_boundary)
{
	struct rtc_time initial = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 129, /* Years since 1900: 2029 */
	};
	struct rtc_time observed;
	int64_t previous;
	int64_t deadline;
	int ret;

	zassert_true(device_is_ready(RTC_DEVICE), "RTC device is not ready");
	ret = rtc_set_time(RTC_DEVICE, &initial);
	zassert_equal(ret, 0, "rtc_set_time failed: %d", ret);

	ret = rtc_get_time(RTC_DEVICE, &observed);
	zassert_equal(ret, 0, "initial rtc_get_time failed: %d", ret);
	previous = rtc_epoch_seconds(&observed);
	zassert_equal(previous, INITIAL_EPOCH_SECONDS,
		       "initial calendar mismatch: got %lld", (long long)previous);

	deadline = k_uptime_get() + OBSERVATION_LIMIT_SECONDS * MSEC_PER_SEC;
	while (previous < INITIAL_EPOCH_SECONDS + 10 && k_uptime_get() < deadline) {
		int64_t current;

		k_sleep(K_MSEC(POLL_INTERVAL_MS));
		ret = rtc_get_time(RTC_DEVICE, &observed);
		zassert_equal(ret, 0, "rtc_get_time failed while observing: %d", ret);
		current = rtc_epoch_seconds(&observed);
		zassert_true(current >= previous,
			     "RTC calendar moved backward: %lld -> %lld",
			     (long long)previous, (long long)current);
		previous = current;
	}

	zassert_true(previous >= INITIAL_EPOCH_SECONDS + 10,
		     "RTC did not advance ten seconds within %d seconds; last value %lld",
		     OBSERVATION_LIMIT_SECONDS, (long long)previous);
	zassert_true(previous >= 1893456000LL,
		     "RTC did not cross into 2030: last value %lld",
		     (long long)previous);
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
