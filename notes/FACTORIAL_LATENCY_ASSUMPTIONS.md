# Non-clock latency assumptions in frozen factorial sources — 2026-10-05

This is a **post-start descriptive recoding** of all 390 frozen sources,
based on the existing source-review evidence. It does not alter the
original functional or timing-bound labels. `yes` requires a
specific unsupported observation/delivery window or asynchronous
ordering premise: exact-second callback read, immediate state
probe, inferred worker entry, short ISR/thread service cutoff,
or timer/workqueue interleaving. A merely finite but generous
deadline with no proved scheduler bound remains `unknown` when the
original review was unknown. Clock-only shortfall without a distinct
latency premise is `not_found` for this category. `Not_found` does
not prove a suite latency-robust. The row CSV preserves every original
source-review explanation and source hash.

| Model | Prompt | Yes | Unknown | Not found | Total |
|---|---|---:|---:|---:|---:|
| astra | range_absent | 23 | 10 | 32 | 65 |
| astra | range_present | 18 | 13 | 34 | 65 |
| luna | range_absent | 27 | 5 | 33 | 65 |
| luna | range_present | 26 | 12 | 27 | 65 |
| sol | range_absent | 27 | 8 | 30 | 65 |
| sol | range_present | 21 | 13 | 31 | 65 |

## Functionally eligible RTC subset (pilot sampling frame)

| Model | Prompt | Yes | Unknown | Not found | Eligible RTC |
|---|---|---:|---:|---:|---:|
| astra | range_absent | 8 | 5 | 2 | 15 |
| astra | range_present | 5 | 6 | 3 | 14 |
| luna | range_absent | 2 | 1 | 1 | 4 |
| luna | range_present | 2 | 0 | 1 | 3 |
| sol | range_absent | 8 | 3 | 4 | 15 |
| sol | range_present | 3 | 9 | 3 | 15 |

A 0/100 result from the clock-only LSI schedule does not clear
this category. For example, `astra-range_absent-rtc_alarm_callback-r01`
has an exact-second callback calendar oracle and had 100/100 seeded
passes in its already completed v2 series. Its source assumption
requires a separate delivery-latency challenge to evaluate.

The historical bound-context supplement's immediate second
`k_sem_take(..., K_NO_WAIT)` after the first asynchronous callback
is a separately recorded example. It is outside the 390 factorial
sources and every factorial rate denominator.
