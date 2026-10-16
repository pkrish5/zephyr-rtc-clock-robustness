#ifndef REFERENCE_RTC_COMMON_H_
#define REFERENCE_RTC_COMMON_H_

#include <zephyr/drivers/rtc.h>
#include <zephyr/kernel.h>

/* 128 * 250 prescaler; LSI endpoints 17 and 47 kHz. One RTC tick of
 * quantization plus five host seconds of experimental service margin gives
 * ceil(11 * 32000 / 17000 + 5) = 26 seconds.
 * Earliest ten-second transition allows one whole tick of phase uncertainty:
 * 9 * 32000 / 47000 = 6127.66 ms; subtract 2 ms for uptime quantization.
 */
#define REFERENCE_CEILING_MS 26000U
#define REFERENCE_EARLIEST_MS 6125U
#define REFERENCE_POLL_MS 20U
#define REFERENCE_ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
	RTC_ALARM_TIME_MASK_MINUTE | RTC_ALARM_TIME_MASK_HOUR)

static const struct rtc_time reference_start = {
	.tm_sec = 55, .tm_min = 59, .tm_hour = 23,
	.tm_mday = 31, .tm_mon = 11, .tm_year = 124,
	.tm_wday = 2, .tm_yday = 365, .tm_isdst = -1,
};
static const struct rtc_time reference_target = {
	.tm_sec = 5, .tm_min = 0, .tm_hour = 0,
	.tm_mday = 1, .tm_mon = 0, .tm_year = 125,
	.tm_wday = 3, .tm_yday = 0, .tm_isdst = -1,
};

static inline bool reference_at_target(const struct rtc_time *t)
{
	if (t->tm_year != 125) { return t->tm_year > 125; }
	if (t->tm_mon != 0) { return t->tm_mon > 0; }
	if (t->tm_mday != 1) { return t->tm_mday > 1; }
	if (t->tm_hour != 0) { return t->tm_hour > 0; }
	if (t->tm_min != 0) { return t->tm_min > 0; }
	return t->tm_sec >= 5;
}

static inline bool reference_crossed_midnight(const struct rtc_time *t)
{
	return t->tm_year >= 125 && t->tm_mon == 0 && t->tm_mday == 1;
}

#endif
