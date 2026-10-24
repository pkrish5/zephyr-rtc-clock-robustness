#include <stdint.h>
#include <time.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/timeutil.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 1
#include "repair_wait.h"

static int64_t calendar_seconds(const struct rtc_time *rtc_time)
{
	struct tm time = {
		.tm_sec = rtc_time->tm_sec,
		.tm_min = rtc_time->tm_min,
		.tm_hour = rtc_time->tm_hour,
		.tm_mday = rtc_time->tm_mday,
		.tm_mon = rtc_time->tm_mon,
		.tm_year = rtc_time->tm_year,
	};

	return timeutil_timegm(&time);
}

ZTEST(rtc_calendar, advances_across_year)
{
	const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 124, /* 2024 */
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_wday = 2,  /* Tuesday */
		.tm_yday = 365,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
	};
	struct rtc_time observed;
	int64_t previous;
	const int64_t start = calendar_seconds(&initial);
	bool crossed;
	bool advanced;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_ok(rtc_set_time(rtc, &initial), "RTC set failed");
	zassert_ok(rtc_get_time(rtc, &observed), "initial RTC read failed");

	previous = calendar_seconds(&observed);
	zassert_true(previous >= start, "initial RTC calendar precedes set time");
	crossed = observed.tm_year > initial.tm_year;
	advanced = previous >= start + 10;

	/* At 17 kHz with a 128 * 250 prescaler, ten RTC seconds take
	 * at most 18.83 real seconds. Allow 30 seconds of requested sleeps
	 * for polling and scheduling overhead; the iteration count is finite.
	 */
	for (int i = 0; !repair_expired() && !(crossed && advanced); ++i) {
		int64_t current;

		k_sleep(K_MSEC(100));
		zassert_ok(rtc_get_time(rtc, &observed), "RTC read failed");
		current = calendar_seconds(&observed);
		zassert_true(current >= previous, "RTC calendar moved backward");
		previous = current;
		crossed |= observed.tm_year > initial.tm_year;
		advanced |= current >= start + 10;
	}

	zassert_true(advanced, "RTC calendar did not advance ten seconds");
	zassert_true(crossed, "RTC calendar did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
