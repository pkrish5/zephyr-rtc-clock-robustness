# Offline audit of the 10-kHz counter-progress control

Date: 2026-11-11. This audit uses the saved source, UART, model and trace. It
does not change the frozen protocol, generate a new result or run Renode.

The preregistered observer band for five 10-kHz ticks is 12,798–16,022 ms.
The verified UART reports `delta_ticks=5 elapsed_ms=16040`: the observation is
18 ms above that upper bound. Five nominal controls report 5,012 ms each
(upper bound 5,022 ms); the 64-kHz control reports 2,516 ms (upper bound
2,522 ms). The slow, nominal and fast observations are ordered as expected,
but ordering cannot override the failed absolute control.

The progress case calls `counter_start`, captures `began = k_uptime_get_32()`,
then reads `first` through `counter_get_value`. It polls another counter read,
checks elapsed uptime, and sleeps 20 ms between attempts. Therefore its
reported interval starts **before** the initial counter sample and ends after
a sampled counter read. The ideal phase interval in the protocol is measured
from the initial sample to the fifth tick. The registered +22-ms observer
allowance covers a nominal polling interval and quantization, but the source
does not establish a hard upper bound on the initial read delay, scheduling,
or execution between the fifth tick and the final uptime read. The driver
converts calendar registers to seconds in `rtc_stm32_read`; it does not emit
timestamps for these source steps. A source-level timing mismatch is thus a
plausible contributor, not a measured explanation for the extra 18 ms.

The saved trace records observations every 0.5 virtual seconds. It shows the
suite still running at 16.0 s and complete by 16.5 s, consistent with the
UART, but cannot locate the first sample, fifth tick or individual 20-ms
polls. The initial RTC divider sample is 32,000; the terminal PRER=0 follows
`counter_stop` and is not evidence that the active divider changed. The
read-only `nvic SystickFrequency` query failed; the sealed platform specifies
16 MHz, but the failed query is not an independent runtime readback.

**Disposition:** existing evidence does not quantitatively explain the 18 ms
or satisfy the frozen upper bound. Activation qualification of the 10-kHz
counter control remains **unresolved**. The selected primary and replay
verdicts (V0 fail, V1 pass, V1b fail, V2 fail) remain valid raw observations,
but are not finalized fault-detection or preservation results for this fourth
case. A new observer, tolerance or control would require a separately
preregistered protocol. No broad legal-clock rerun is needed to report the
observed legal repair.

Evidence: `PROTOCOL.md`, `report-3575326-v1/summary.json`,
`verified-3575326-v1/output/new_sources/subjects/counter_verification_20261111_v1/progress.c`,
`verified-3575326-v1/output/new_sources/subjects/counter_verification_20261111_v1/common.h`,
`verified-3575326-v1/output/references/uart/f4-progress-control-slow_progress_control-027.log`,
`verified-3575326-v1/output/references/traces/f4-progress-control-slow_progress_control-027.json`,
and `subjects/upstream/zephyr/drivers/counter/counter_ll_stm32_rtc.c`.
