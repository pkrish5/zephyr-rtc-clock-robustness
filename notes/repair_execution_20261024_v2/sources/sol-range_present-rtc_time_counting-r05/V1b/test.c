#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

#define REPAIR_EVENT_WAIT 0
#include "repair_wait.h"

static int calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = { a->tm_year, a->tm_mon, a->tm_mday,
			   a->tm_hour, a->tm_min, a->tm_sec };
	const int bv[] = { b->tm_year, b->tm_mon, b->tm_mday,
			   b->tm_hour, b->tm_min, b->tm_sec };

	for (int i = 0; i < 6; i++) {
		if (av[i] != bv[i]) {
			return (av[i] > bv[i]) ? 1 : -1;
		}
	}
	return 0;
}

ZTEST(rtc_calendar, advances_across_year_boundary)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time initial = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2,
	};
	const struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time previous;
	struct rtc_time current;
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_ok(rtc_set_time(rtc, &initial), "RTC set failed");
	zassert_ok(rtc_get_time(rtc, &previous), "initial RTC read failed");
	zassert_true(calendar_cmp(&previous, &initial) >= 0,
		     "initial RTC calendar is earlier than the set time");

	/* At 17 kHz with a 128 x 250 prescaler, ten RTC seconds take
	 * under 19 wall seconds. Allow 30 seconds for polling and scheduling.
	 */
	deadline = repair_deadline;
	do {
		zassert_true(k_uptime_get() < deadline,
			     "RTC did not reach ten seconds within 30 seconds");
		k_sleep(K_MSEC(100));
		zassert_ok(rtc_get_time(rtc, &current), "RTC read failed");
		zassert_true(calendar_cmp(&current, &previous) >= 0,
			     "RTC calendar moved backward");
		previous = current;
	} while (calendar_cmp(&current, &target) < 0);

	zassert_true(current.tm_year >= 125,
		     "RTC did not cross the year boundary");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
