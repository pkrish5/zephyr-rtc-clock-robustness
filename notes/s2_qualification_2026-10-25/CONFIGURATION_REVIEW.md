# S2 configuration review from generated build records

This is static/generated-build evidence, not a completed qualification result.
Source files are unchanged. Generated file hashes match their saved build records.

## Non-stock RTC-only counter selection

Both counter applications explicitly select CONFIG_COUNTER_RTC_STM32=y,
CONFIG_COUNTER_RTC_STM32_SUBSECONDS=n, CONFIG_COUNTER_TIMER_STM32=n and
CONFIG_RTC=n. DTC_OVERLAY_FILE selects the registered overlay rather than the
application's stock board overlay. The aliases rtc and rtc-0 select the RTC.
All source cases remain compiled, and the normal capability checks remain active.
This configuration must be described as non-stock in the later manuscript.

## F072 divider policy, pending runtime confirmation

The actual generated DTS for all three F072 builds declares clk_lsi at 40000 Hz
and has neither async-prescaler nor sync-prescaler on rtc. The source defaults
therefore apply, without compensating overrides:

- RTC API: drivers/rtc/rtc_ll_stm32.c:1133-1137 uses async127, sync249 for LSI,
  giving 128*250=32000. At the chip's nominal40000Hz input, the calendar rate is
  1.25 RTC seconds per virtual second. Nominal assertion failures are retained.
- RTC counter: drivers/counter/counter_ll_stm32_rtc.c:76-99 derives RTCCLK_FREQ
  from STM32_LSI_FREQ, sets async127 and computes sync=40000/128-1 with integer
  division, giving 311 and total divider39936. The clock header at
  include/zephyr/drivers/clock_control/stm32_clock_control.h:606-608 takes this
  frequency from the generated clk_lsi clock-frequency. This does not silently
  rescale the RTC API driver or an existing test.

A final resolution still requires observed PRER values and the five nominal/
seven calibration outcomes. Do not mark F072 production-qualified on static
build evidence alone. The registered range is30000..50000Hz, nominal40000Hz.

## CPU-time reference

Generated SYS_CLOCK_HW_CYCLES_PER_SEC is16000000 for F4,48000000 for F072 and
480000000 for H753; other board configs remain stock. The inspected counter
configs have CORTEX_M_DWT disabled. Their generic busy wait reads k_cycle_get_32
(kernel/busy_wait.c:12-33), and the selected SysTick driver provides that clock
(drivers/timer/cortex_m_systick.c:438-445). Timing checks must use actual source
waits, integer conversions, phase and the board-specific divider; do not assume
every test has one monotonic scalar boundary. Capability checks can themselves
contain waits, so report clock-dependent skips separately from assertions.

## H753 frozen envelope

DS12117 Rev10 revision V input envelope, VDD1.62..3.6V, TJ -40..105C,
29760..33600Hz, nominal32000Hz. This is a modeled input envelope, not a physical
silicon identification. Saved DBGMCU reads are evidence of model behavior only.

## Generated artifact hashes

| Build | .config SHA-256 | zephyr.dts SHA-256 |
|---|---|---|
| f4-rtc | 5196a052af124d588180d720cfdc810f367d3ea95cff5a1b02811ac7cb5c6657 | bb6c76fedf4f8a524f012f08a69619e997439e92e383be03ae83cbcf8b3e0924 |
| f072-rtc | 50440091086a00428ed9ef338fdd94be91e4655919b8d64dcd460de1d95fd08f | 750d41d9a2ef7e92a0606a0cedd3582a3206e128a3078d7c73f701dae9413a9f |
| f072-counter | 0093d3e60bdb9c4bacb4763f1c17d05ca8dab8d3e8bf21e3d43d7eba75ba16eb | 750d41d9a2ef7e92a0606a0cedd3582a3206e128a3078d7c73f701dae9413a9f |
| f072-seconds | 067022fcca93997c31d382b23ccbea33512335a5024e32fbc9796a31eb08e74a | 750d41d9a2ef7e92a0606a0cedd3582a3206e128a3078d7c73f701dae9413a9f |
| h753-rtc | 1657bcae20435bb93cff28603979e22c4a01b6c2f0fefb0f629789232d1cae94 | 5d3de8444b919cdd3d68c9a344bdc4e674f92f5e4a83875ef58d7bcef1c63e83 |
| h753-counter | 9eecffbd0b793eaf90edb6a6a5348edfdcb825f13b5dbe8bb7dc4bf01e59766f | 5d3de8444b919cdd3d68c9a344bdc4e674f92f5e4a83875ef58d7bcef1c63e83 |
