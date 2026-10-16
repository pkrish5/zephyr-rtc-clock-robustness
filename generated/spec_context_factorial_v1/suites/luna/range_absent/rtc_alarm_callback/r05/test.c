#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_COUNT 2
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)
#define EXPECTED_ALARMS ((1U << ALARM_COUNT) - 1U)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem alarm_events;
static atomic_t alarm_ids;

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (id < ALARM_COUNT) {
		atomic_or(&alarm_ids, (atomic_val_t)(1U << id));
		k_sem_give(&alarm_events);
	}
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
	struct rtc_time now = {
		.tm_sec = 55,
		.tm_min = 59,
		.tm_hour = 23,
		.tm_mday = 31,
		.tm_mon = 11,
		.tm_year = 124,
	};
	struct rtc_time alarm = {
		.tm_sec = 5,
		.tm_min = 0,
		.tm_hour = 0,
		.tm_mday = 1,
		.tm_mon = 0,
		.tm_year = 125,
	};

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	k_sem_init(&alarm_events, 0, ALARM_COUNT);
	atomic_set(&alarm_ids, 0);

	zassert_ok(rtc_set_time(rtc, &now), "Failed to set RTC calendar");
	for (uint16_t id = 0; id < ALARM_COUNT; id++) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback, NULL),
			   "Failed to set callback for alarm %u", id);
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
			   "Failed to set alarm %u", id);
	}

	/* The target is ten RTC seconds away; this checks for early callbacks. */
	zassert_equal(k_sem_take(&alarm_events, K_SECONDS(2)), -EAGAIN,
		      "An alarm fired before its configured time");
	zassert_equal(atomic_get(&alarm_ids), 0,
		      "An alarm callback was observed prematurely");

	/* Allow the ten-second interval plus five seconds for LSI/scheduling slack. */
	for (int i = 0; i < ALARM_COUNT; i++) {
		zassert_ok(k_sem_take(&alarm_events, K_SECONDS(15)),
			   "Timed out waiting for alarm callback %d", i);
	}
	zassert_equal(atomic_get(&alarm_ids), EXPECTED_ALARMS,
		      "Callbacks did not report both expected alarm IDs");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
