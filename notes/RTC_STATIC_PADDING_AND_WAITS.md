# Static RTC padding and wait inventory — 2026-10-05

This is a source-only descriptive analysis. The frozen forecast ledger supplies
a single clock-only observation budget for 30 of 66 functionally eligible RTC
suites. The other 36 have no defensible scalar budget under LSI rate alone
and remain `unknown` for this padding metric. The per-suite CSV retains
every denominator member and source expression.

For a ten-calendar-second target, the slow legal LSI endpoint requires `10 × 32000 / 17000 = 18.823529` host seconds in the ideal
clock model. Define the descriptive padding ratio as source observation
budget divided by this bound. A ratio strictly greater than 2 is coded
`over_padded`. This threshold is an analysis convention, not a hardware
upper limit or proof that a lower ratio is adequate. It excludes phase,
polling, scheduling, and callback latency; source labels with no scalar
budget are left unknown. Thus it cannot certify a timing oracle.

| Model | Prompt | Over padded | At or below 2× | Unknown | Rate among assessable |
|---|---|---:|---:|---:|---:|
| astra | range_absent | 5 | 1 | 9 | 5/6 (83.3%) |
| astra | range_present | 0 | 5 | 9 | 0/5 (0.0%) |
| luna | range_absent | 0 | 4 | 0 | 0/4 (0.0%) |
| luna | range_present | 3 | 0 | 0 | 3/3 (100.0%) |
| sol | range_absent | 2 | 5 | 8 | 2/7 (28.6%) |
| sol | range_present | 2 | 3 | 10 | 2/5 (40.0%) |

The [wait-style ledger](../analysis/rtc_static_waits.csv) records
source-pattern flags and the median of existing saved nominal pass
wall times for each eligible AI suite, plus the separately
qualified nominal logs for the three human selected cases. It
makes no new simulation runs. A source may have multiple wait styles.

| Model | Prompt | Eligible suites | Fixed sleep syntax | Event-wait API syntax | Median of per-suite nominal medians (wall s) |
|---|---|---:|---:|---:|---:|
| astra | range_absent | 15 | 10 | 5 | 38.19 |
| astra | range_present | 14 | 12 | 2 | 38.52 |
| luna | range_absent | 4 | 4 | 0 | 38.19 |
| luna | range_present | 3 | 3 | 0 | 40.74 |
| sol | range_absent | 15 | 15 | 1 | 38.08 |
| sol | range_present | 15 | 13 | 5 | 37.91 |

These syntax flags can overlap. In particular, an event API
called with `K_NO_WAIT` is counted as syntax, not as a genuine
blocking wait. The per-suite CSV is the authoritative runtime
inventory; a cell median does not replace it.
