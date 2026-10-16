# Pinned Zephyr static timing threshold scan — 2026-10-05

This scan reads source only; it does not run Zephyr or establish
hardware-specific limits for other boards. Its exact scope is the
seven pinned test trees below, including C/C++ sources and headers.
Python host tests, generated files, and other Zephyr test trees are
outside scope. The CSV records line candidates and SHA-256 per file.

| Test tree | Source files |
|---|---:|
| `tests/boards/native_sim/rtc` | 1 |
| `tests/drivers/build_all/counter` | 1 |
| `tests/drivers/build_all/rtc` | 1 |
| `tests/drivers/counter` | 4 |
| `tests/drivers/rtc` | 14 |
| `tests/drivers/timer` | 2 |
| `tests/kernel/timer` | 10 |

| Review status | Files |
|---|---:|
| needs_manual_bound | 23 |
| no_pattern_found | 7 |
| selected_case_clock_bound_shortfall | 3 |

The three selected STM32 RTC sources have fixed observation
boundaries of 13, 13, and 14.5 host seconds, below the ideal
10-second calendar transition at the legal slow endpoint
(`18.823529` host seconds). That shortfall identifies a
clock-bound threshold risk, not a full behavior verdict. Every
other hit remains `needs_manual_bound`; a literal timeout alone
cannot be judged against an unspecified clock or API guarantee.
