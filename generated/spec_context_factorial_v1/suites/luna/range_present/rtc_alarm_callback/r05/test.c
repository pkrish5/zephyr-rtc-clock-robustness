#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_TIMEOUT K_SECONDS(25)

static struct k_sem alarm_sem;
static atomic_t callback_bits;
static atomic_t unexpected_callback;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id > 1U) {
		atomic_set(&unexpected_callback, 1);
		return;
	}

	atomic_or(&callback_bits, BIT(id));
	k_sem_give(&alarm_sem);
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time now = {0};
	struct rtc_time alarm = {0};
	struct rtc_time after = {0};
	int64_t deadline;
	int rc;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");

	k_sem_init(&alarm_sem, 0, 2);
	atomic_set(&callback_bits, 0);
	atomic_set(&unexpected_callback, 0);

	zassert_ok(rtc_alarm_set_callback(rtc, 0, alarm_callback, NULL),
		   "Could not set callback for alarm 0");
	zassert_ok(rtc_alarm_set_callback(rtc, 1, alarm_callback, NULL),
		   "Could not set callback for alarm 1");

	/* rtc_time uses years since 1900 and months in the range 0..11. */
	now.tm_year = 124;
	now.tm_mon = 11;
	now.tm_mday = 31;
	now.tm_hour = 23;
	now.tm_min = 59;
	now.tm_sec = 55;
	alarm.tm_year = 125;
	alarm.tm_mon = 0;
	alarm.tm_mday = 1;
	alarm.tm_hour = 0;
	alarm.tm_min = 0;
	alarm.tm_sec = 5;

	zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm),
		   "Could not set alarm 0");
	zassert_ok(rtc_alarm_set_time(rtc, 1, ALARM_MASK, &alarm),
		   "Could not set alarm 1");
	zassert_ok(rtc_set_time(rtc, &now), "Could not set RTC calendar time");

	/* One second is well short of the ten RTC seconds to the alarm, even at
	 * the documented fastest LSI rate (47 kHz with a 128 x 250 prescaler).
	 */
	k_sleep(K_SECONDS(1));
	zassert_equal(atomic_get(&callback_bits), 0,
		      "An alarm callback arrived before the alarm time");
	zassert_equal(atomic_get(&unexpected_callback), 0,
		      "Callback reported an unconfigured alarm ID");
	zassert_ok(rtc_get_time(rtc, &after), "Could not read RTC time");
	zassert_true(after.tm_year == 124 && after.tm_mon == 11 &&
		     after.tm_mday == 31 && after.tm_hour == 23 &&
		     after.tm_min == 59 && after.tm_sec < 5,
		     "RTC reached the alarm time before the premature check");

	/* At the slowest documented LSI rate, ten RTC seconds take about
	 * 18.9 seconds. The 25-second deadline allows additional time for
	 * interrupt and thread delivery; the API documents no delivery bound.
	 */
	deadline = k_uptime_get() + k_ticks_to_ms_floor64(ALARM_TIMEOUT.ticks);
	for (int i = 0; i < 2; i++) {
		int64_t remaining = deadline - k_uptime_get();

		zassert_true(remaining > 0, "Timed out waiting for both alarms");
		rc = k_sem_take(&alarm_sem, K_MSEC(remaining));
		zassert_ok(rc, "Timed out waiting for both alarms");
	}

	zassert_equal(atomic_get(&callback_bits), BIT(0) | BIT(1),
		      "Callbacks did not report both configured alarm IDs");
	zassert_equal(atomic_get(&unexpected_callback), 0,
		      "Callback reported an unconfigured alarm ID");
	zassert_ok(rtc_get_time(rtc, &after), "Could not read RTC time");
	zassert_true(after.tm_year > 125 ||
		     (after.tm_year == 125 &&
		      (after.tm_mon > 0 ||
		       (after.tm_mon == 0 &&
			(after.tm_mday > 1 ||
			 (after.tm_mday == 1 &&
			  (after.tm_hour > 0 ||
			   (after.tm_hour == 0 &&
			    (after.tm_min > 0 ||
			     (after.tm_min == 0 && after.tm_sec >= 5))))))))),
		     "Callbacks arrived before the configured RTC alarm time");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
