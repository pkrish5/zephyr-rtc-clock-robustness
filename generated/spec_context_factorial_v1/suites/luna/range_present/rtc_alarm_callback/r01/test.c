#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_COUNT 2
#define EXPECTED_CALLBACKS ((1U << ALARM_COUNT) - 1U)

/*
 * At the slowest characterized LSI rate, one RTC second takes about
 * 32,000 / 17,000 = 1.883 real seconds. Ten RTC seconds therefore take
 * at most 18.83 seconds. The additional 3 seconds allows for polling and
 * thread scheduling; Zephyr does not specify a bound on ISR delivery latency.
 */
#define ALARM_WAIT_BOUND K_SECONDS(22)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static atomic_t callback_mask;
static struct k_sem callback_sem;

static void alarm_callback(const struct device *dev, uint16_t alarm_id,
                           void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);

	if (alarm_id < ALARM_COUNT) {
		atomic_or(&callback_mask, BIT(alarm_id));
		k_sem_give(&callback_sem);
	}
}

ZTEST(rtc_alarm_callbacks, test_both_alarm_channels)
{
	struct rtc_time calendar = {
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
	const uint16_t mask = RTC_ALARM_TIME_MASK_SECOND |
			     RTC_ALARM_TIME_MASK_MINUTE |
			     RTC_ALARM_TIME_MASK_HOUR;
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	atomic_set(&callback_mask, 0);
	k_sem_init(&callback_sem, 0, ALARM_COUNT);
	zassert_ok(rtc_set_time(rtc, &calendar), "Failed to set RTC calendar");

	for (uint16_t id = 0; id < ALARM_COUNT; id++) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback, NULL),
			   "Failed to set callback for alarm %u", id);
		zassert_ok(rtc_alarm_set_time(rtc, id, mask, &alarm),
			   "Failed to set time for alarm %u", id);
	}

	/* One real second is less than two RTC seconds even at maximum LSI. */
	k_sleep(K_SECONDS(1));
	zassert_equal(atomic_get(&callback_mask), 0,
		      "An alarm callback fired before the configured time");

	deadline = k_uptime_get() + k_ticks_to_ms_floor64(ALARM_WAIT_BOUND.ticks);
	while (atomic_get(&callback_mask) != EXPECTED_CALLBACKS &&
	       k_uptime_get() < deadline) {
		(void)k_sem_take(&callback_sem, K_MSEC(10));
	}

	zassert_equal(atomic_get(&callback_mask), EXPECTED_CALLBACKS,
		      "Both alarm callbacks were not received within the finite wait bound");
	zassert_true(rtc_alarm_is_pending(rtc, 0), "Alarm 0 is not pending");
	zassert_true(rtc_alarm_is_pending(rtc, 1), "Alarm 1 is not pending");
}

ZTEST_SUITE(rtc_alarm_callbacks, NULL, NULL, NULL, NULL, NULL);
