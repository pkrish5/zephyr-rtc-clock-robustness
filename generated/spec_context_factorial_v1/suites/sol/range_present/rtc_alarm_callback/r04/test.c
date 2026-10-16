#include <zephyr/device.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define RTC_NODE DT_ALIAS(rtc)
#define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

struct alarm_observation {
	uint16_t expected_id;
	atomic_t count;
	atomic_t wrong_id;
	int read_result;
	struct rtc_time when;
};

static struct alarm_observation observed[2];
K_SEM_DEFINE(alarm_events, 0, 2);

static bool before_alarm(const struct rtc_time *t)
{
	return t->tm_year == 124 ||
	       (t->tm_year == 125 && t->tm_mon == 0 && t->tm_mday == 1 &&
		t->tm_hour == 0 && t->tm_min == 0 && t->tm_sec < 5);
}

static void alarm_callback(const struct device *dev, uint16_t id, void *user_data)
{
	struct alarm_observation *obs = user_data;

	if (id != obs->expected_id) {
		atomic_set(&obs->wrong_id, 1);
	}
	obs->read_result = rtc_get_time(dev, &obs->when);
	atomic_inc(&obs->count);
	k_sem_give(&alarm_events);
}

ZTEST(rtc_alarm, both_alarms_at_new_year)
{
	const struct device *rtc = DEVICE_DT_GET(RTC_NODE);
	struct rtc_time setup_time = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 50, .tm_sec = 0,
	};
	struct rtc_time start_time = {
		.tm_year = 124, .tm_mon = 11, .tm_mday = 31,
		.tm_hour = 23, .tm_min = 59, .tm_sec = 55,
	};
	struct rtc_time alarm_time = {
		.tm_year = 125, .tm_mon = 0, .tm_mday = 1,
		.tm_hour = 0, .tm_min = 0, .tm_sec = 5,
	};
	struct rtc_time now;
	int64_t deadline;

	zassert_true(device_is_ready(rtc), "RTC is not ready");
	zassert_ok(rtc_set_time(rtc, &setup_time));

	for (uint16_t id = 0; id < 2; id++) {
		observed[id].expected_id = id;
		atomic_set(&observed[id].count, 0);
		atomic_set(&observed[id].wrong_id, 0);
		zassert_ok(rtc_alarm_set_time(rtc, id, ALARM_MASK, &alarm_time));
		zassert_ok(rtc_alarm_set_callback(rtc, id, alarm_callback,
					   &observed[id]));
	}

	zassert_ok(rtc_set_time(rtc, &start_time));
	/* Ten RTC seconds take at most 10 * 32000 / 17000 = 18.83 s.
	 * The 30 s deadline also allows 11.17 s for callback delivery.
	 */
	deadline = k_uptime_get() + 30000;
	while (true) {
		atomic_val_t count0 = atomic_get(&observed[0].count);
		atomic_val_t count1 = atomic_get(&observed[1].count);

		zassert_ok(rtc_get_time(rtc, &now));
		if (!before_alarm(&now)) {
			break;
		}
		zassert_equal(count0, 0, "alarm 0 fired early");
		zassert_equal(count1, 0, "alarm 1 fired early");
		zassert_true(k_uptime_get() < deadline, "RTC did not reach alarm time");
		k_sleep(K_MSEC(20));
	}

	for (int i = 0; i < 2; i++) {
		int64_t remaining = deadline - k_uptime_get();

		zassert_true(remaining > 0, "alarm callback timed out");
		zassert_ok(k_sem_take(&alarm_events, K_MSEC(remaining)),
			   "alarm callback timed out");
	}

	for (int i = 0; i < 2; i++) {
		const struct alarm_observation *obs = &observed[i];

		zassert_equal(atomic_get(&obs->count), 1, "alarm callback count");
		zassert_equal(atomic_get(&obs->wrong_id), 0, "wrong alarm ID");
		zassert_ok(obs->read_result, "callback could not read RTC");
		zassert_equal(obs->when.tm_year, 125);
		zassert_equal(obs->when.tm_mon, 0);
		zassert_equal(obs->when.tm_mday, 1);
		zassert_equal(obs->when.tm_hour, 0);
		zassert_equal(obs->when.tm_min, 0);
		zassert_equal(obs->when.tm_sec, 5);
	}
}

ZTEST_SUITE(rtc_alarm, NULL, NULL, NULL, NULL, NULL);
