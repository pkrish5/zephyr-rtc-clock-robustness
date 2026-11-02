/* SPDX-License-Identifier: Apache-2.0 */
#ifndef S2_REFERENCE_COMMON_H
#define S2_REFERENCE_COMMON_H
#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

/* Experimental service margins, not a claim of bounded physical ISR latency.
 * Cohort envelope: fixed divider 32000, input 17000..47000 Hz.
 * Ten calendar ticks: ceil(11*32000/17000 + 5) = 26 seconds.
 * Earliest ten ticks with one tick phase uncertainty: 9*32000/47000,
 * minus 2 ms of observation/uptime quantization.
 * A two-tick relative counter request adds a driver tick; one additional
 * uncertainty tick plus 5 seconds gives ceil(4*32000/17000 + 5)=13 seconds.
 */
#define REF_TEN_TICK_CEILING_MS 26000U
#define REF_TEN_TICK_EARLIEST_MS 6125U
#define REF_COUNTER_CEILING_MS 13000U
#define REF_TWO_TICK_EARLIEST_MS 1360U
#define REF_POLL_MS 20U

static inline uint32_t ref_elapsed(uint32_t start)
{
	return k_uptime_get_32() - start;
}
#endif
