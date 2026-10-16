#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
		    RTC_ALARM_TIME_MASK_MINUTE | \
		    RTC_ALARM_TIME_MASK_HOUR)
#define ALARM_COUNT 2
#define DELIVERY_TIMEOUT K_SECONDS(2)

static const struct device *const rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
static struct k_sem alarm_event;
static atomic_t callback_mask;
static atomic_t callback_ids[ALARM_COUNT];

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);
	if (id < ALARM_COUNT) {
		atomic_set(&callback_ids[id], 1);
		atomic_or(&callback_mask, BIT(id));
		k_sem_give(&alarm_event);
	}
}

ZTEST(rtc_alarm, test_both_alarm_channels)
{
	struct rtc_time now = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	};
	const struct rtc_time alarm = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};

	zassert_true(device_is_ready(rtc), "RTC device is not ready");
	k_sem_init(&alarm_event, 0, ALARM_COUNT);
	atomic_clear(&callback_mask);
	for (uint32_t i = 0; i < ALARM_COUNT; ++i) {
		atomic_clear(&callback_ids[i]);
		zassert_ok(rtc_alarm_set_callback(rtc, i, alarm_callback, NULL),
			   "register callback for alarm %u", i);
		zassert_ok(rtc_alarm_set_time(rtc, i, &alarm, ALARM_MASK),
			   "set alarm %u", i);
	}
	zassert_ok(rtc_set_time(rtc, &now), "set RTC calendar time");

	/* Allow the eight-second calendar interval at the slowest documented
	 * LSI rate: 32 kHz / (128 * 250) = 1 Hz, plus one second margin.
	 */
	k_sleep(K_SECONDS(1));
	zassert_equal(atomic_get(&callback_mask), 0,
		      "alarm callback observed before configured time");
	zassert_equal(rtc_alarm_is_pending(rtc, 0), 0,
		      "alarm 0 pending prematurely");
	zassert_equal(rtc_alarm_is_pending(rtc, 1), 0,
		      "alarm 1 pending prematurely");

	/* Eight RTC seconds need at most 128*250/17000*8 = 15.06 s.
	 * Add two seconds for calendar/interrupt delivery, since oscillator
	 * frequency does not itself bound ISR-to-thread latency.
	 */
	for (int i = 0; i < ALARM_COUNT; ++i) {
		zassert_true(k_sem_take(&alarm_event, DELIVERY_TIMEOUT) == 0,
			    "timed out waiting for an alarm callback");
	}
	zassert_equal(atomic_get(&callback_mask), BIT(0) | BIT(1),
		      "callbacks did not identify both configured alarm IDs");
	zassert_equal(atomic_get(&callback_ids[0]), 1, "alarm 0 callback missing");
	zassert_equal(atomic_get(&callback_ids[1]), 1, "alarm 1 callback missing");
	zassert_ok(rtc_get_time(rtc, &now), "read RTC calendar time");
	zassert_equal(now.tm_year, alarm.tm_year, "unexpected alarm year");
	zassert_equal(now.tm_mon, alarm.tm_mon, "unexpected alarm month");
	zassert_equal(now.tm_mday, alarm.tm_mday, "unexpected alarm day");
	zassert_equal(now.tm_hour, alarm.tm_hour, "unexpected alarm hour");
	zassert_equal(now.tm_min, alarm.tm_min, "unexpected alarm minute");
	zassert_equal(now.tm_sec, alarm.tm_sec, "unexpected alarm second");
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
