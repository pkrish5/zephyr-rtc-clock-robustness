#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

static int calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
{
#define CMP(field) do { if (a->field != b->field) return a->field < b->field ? -1 : 1; } while (0)
	CMP(tm_year);
	CMP(tm_mon);
	CMP(tm_mday);
	CMP(tm_hour);
	CMP(tm_min);
	CMP(tm_sec);
#undef CMP
	return 0;
}

ZTEST(rtc_calendar, test_year_boundary_counting)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	const struct rtc_time start = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
		.tm_wday = 2, .tm_yday = 365,
	};
	const struct rtc_time target = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time previous;
	struct rtc_time current;
	bool reached = false;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_ok(rtc_set_time(rtc, &start), "RTC set failed");
	zassert_ok(rtc_get_time(rtc, &previous), "initial RTC read failed");
	zassert_true(calendar_cmp(&previous, &start) >= 0,
		     "initial calendar precedes the set time");

	/* At 17 kHz with a 128 * 250 prescaler, ten RTC seconds
	 * take at most 10 * 32000 / 17000 = 18.83 real seconds.
	 * Up to 160 polling sleeps provide 40 seconds of sleep time.
	 * Polling does not depend on RTC interrupt delivery latency.
	 */
	for (int i = 0; i < 160; ++i) {
		k_sleep(K_MSEC(250));
		zassert_ok(rtc_get_time(rtc, &current), "RTC read failed");
		zassert_true(calendar_cmp(&current, &previous) >= 0,
			     "RTC calendar moved backward");
		if (calendar_cmp(&current, &target) >= 0) {
			reached = true;
			break;
		}
		previous = current;
	}

	zassert_true(reached, "RTC did not advance ten seconds across New Year");
}

ZTEST_SUITE(rtc_calendar, NULL, NULL, NULL, NULL, NULL);
