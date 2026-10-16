#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define ALARM_COUNT 2
#define OBSERVATION_MS 30000
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
                    RTC_ALARM_TIME_MASK_MINUTE | \
                    RTC_ALARM_TIME_MASK_HOUR)

struct callback_state {
	struct k_sem event;
	atomic_t reported_id;
};

static struct callback_state states[ALARM_COUNT];

static void alarm_callback(const struct device *dev, uint16_t id,
			   void *user_data)
{
	struct callback_state *state = user_data;

	(void)dev;
	atomic_set(&state->reported_id, id);
	k_sem_give(&state->event);
}

ZTEST(rtc_alarm, test_both_channels_across_new_year)
{
	const struct device *rtc = DEVICE_DT_GET(DT_ALIAS(rtc));
	struct rtc_time now = {
		.tm_year = 2024 - 1900,
		.tm_mon = 11,
		.tm_mday = 31,
		.tm_hour = 23,
		.tm_min = 59,
		.tm_sec = 55,
		.tm_wday = 2,
		.tm_yday = 365,
		.tm_isdst = -1,
		.tm_nsec = 0,
	};
	struct rtc_time alarm = {
		.tm_year = 2025 - 1900,
		.tm_mon = 0,
		.tm_mday = 1,
		.tm_hour = 0,
		.tm_min = 0,
		.tm_sec = 5,
		.tm_wday = 3,
		.tm_yday = 0,
		.tm_isdst = -1,
		.tm_nsec = 0,
	};
	int observed[ALARM_COUNT];
	int disabled[ALARM_COUNT];
	int detached[ALARM_COUNT];

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_equal(ALARM_MASK, 7, "Unexpected alarm mask");

	/* Disable both channels and consume any pre-existing pending events. */
	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, NULL, NULL),
			   "Cannot detach callback %u", (unsigned int)id);
		zassert_ok(rtc_alarm_set_time(rtc, id, 0, NULL),
			   "Cannot disable alarm %u", (unsigned int)id);
		zassert_true(rtc_alarm_is_pending(rtc, id) >= 0,
			     "Cannot clear pending alarm %u", (unsigned int)id);
		k_sem_init(&states[id].event, 0, 1);
		atomic_set(&states[id].reported_id, -1);
	}

	zassert_ok(rtc_set_time(rtc, &now), "Cannot set RTC calendar");

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm),
			   "Cannot program alarm %u", (unsigned int)id);
	}

	/* Register only after both alarms have been programmed. */
	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
						 &states[id]),
			   "Cannot register callback %u", (unsigned int)id);
	}

	/* One shared finite window, with margin for the independent LSI. */
	int64_t deadline = k_uptime_get() + OBSERVATION_MS;

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		int64_t remaining = deadline - k_uptime_get();

		observed[id] = k_sem_take(&states[id].event,
			remaining > 0 ? K_MSEC(remaining) : K_NO_WAIT);
	}

	/* Quiesce callbacks before evaluating results, including on timeout. */
	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		disabled[id] = rtc_alarm_set_time(rtc, id, 0, NULL);
		detached[id] = rtc_alarm_set_callback(rtc, id, NULL, NULL);
	}

	for (uint16_t id = 0; id < ALARM_COUNT; ++id) {
		zassert_ok(observed[id], "Callback %u was not observed",
			   (unsigned int)id);
		zassert_equal(atomic_get(&states[id].reported_id), id,
			      "Callback %u reported the wrong alarm ID",
			      (unsigned int)id);
		zassert_ok(disabled[id], "Alarm cleanup failed");
		zassert_ok(detached[id], "Callback cleanup failed");
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
