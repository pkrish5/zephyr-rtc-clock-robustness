/* Registered mechanical waiting adapter; original assertions remain below.
 * Original timeout messages may still describe V0's budget.
 */
#ifndef REPAIR_WAIT_H
#define REPAIR_WAIT_H
#include <zephyr/kernel.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/sys/util.h>
#include <stdint.h>
#include <stdbool.h>
static int64_t repair_deadline;
static int repair_set_time(const struct device *dev, const struct rtc_time *value)
{
    repair_deadline = k_uptime_get() + 20824;
    return rtc_set_time(dev, value);
}
static inline bool repair_expired(void)
{
    return k_uptime_get() >= repair_deadline;
}
static int32_t repair_sleep(k_timeout_t requested)
{
    int64_t wait_ms = k_ticks_to_ms_ceil64(requested.ticks);
    int64_t remaining = MAX(INT64_C(0), repair_deadline - k_uptime_get());
    if (REPAIR_EVENT_WAIT) {
        wait_ms = MIN(wait_ms, INT64_C(20));
    }
    return k_sleep(K_MSEC(MIN(wait_ms, remaining)));
}
static inline void repair_fixed_wait(void)
{
    k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));
}
#define rtc_set_time repair_set_time
#define k_sleep repair_sleep
#define k_msleep(ms) repair_sleep(K_MSEC(ms))
#endif
