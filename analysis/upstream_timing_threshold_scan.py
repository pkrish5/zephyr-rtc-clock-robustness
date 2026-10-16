#!/usr/bin/env python3
"""Conservative source-only scan of pinned Zephyr RTC, counter and timer tests.

The output is a review queue. Only the three selected STM32 RTC cases have a
registered clock transition and board-specific LSI bound in this study.
"""

import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZEPHYR = ROOT / "subjects/upstream/zephyr/tests"
OUT = ROOT / "analysis/upstream_timing_threshold_scan.csv"
REPORT = ROOT / "notes/UPSTREAM_STATIC_THRESHOLD_SCAN.md"
TEST_ROOTS = (
    "drivers/rtc", "drivers/counter", "drivers/timer", "kernel/timer",
    "drivers/build_all/rtc", "drivers/build_all/counter", "boards/native_sim/rtc",
)
SOURCE_EXT = {".c", ".h", ".cpp"}
PATTERNS = {
    "sleep_or_busy_wait": re.compile(r"\bk_(?:sleep|msleep|usleep|busy_wait)\s*\("),
    "event_timeout": re.compile(r"\bk_(?:sem_take|poll|event_wait|msgq_get|fifo_get)\s*\("),
    "timer_api": re.compile(r"\bk_timer_(?:start|status_sync|stop)\s*\("),
    "rtc_or_counter": re.compile(r"\b(?:rtc|counter)_[a-z_]+\s*\("),
    "literal_duration": re.compile(r"\bK_(?:MSEC|USEC|SECONDS|MINUTES)\s*\(\s*\d+\s*\)"),
    "time_assertion": re.compile(r"\b(?:zassert|__ASSERT)[a-z_]*\s*\([^\n]*(?:time|timeout|early|late|pending|expire|callback)", re.I),
}
KNOWN = {
    "drivers/rtc/rtc_api/src/test_alarm_callback.c":
        (13.0, "two fixed sleeps, 3 + 10 host seconds, before callback assertion"),
    "drivers/rtc/rtc_api/src/test_alarm.c":
        (13.0, "two fixed sleeps, 3 + 10 host seconds, before pending assertion"),
    "drivers/rtc/rtc_api/src/test_time_incrementing.c":
        (14.5, "last of 30 polls occurs after 29 × 0.5 host seconds"),
}
WORST_CASE_S = 10 * 32000 / 17000


def main():
    rows = []
    for test_root in TEST_ROOTS:
        for source_path in sorted((ZEPHYR / test_root).rglob("*")):
            if source_path.suffix not in SOURCE_EXT or not source_path.is_file():
                continue
            source = source_path.read_text(errors="replace")
            rel = str(source_path.relative_to(ZEPHYR))
            hits = {name: [i for i, line in enumerate(source.splitlines(), 1)
                           if pattern.search(line)]
                    for name, pattern in PATTERNS.items()}
            if rel in KNOWN:
                budget, basis = KNOWN[rel]
                status = "selected_case_clock_bound_shortfall"
                assert budget < WORST_CASE_S
            elif any(hits.values()):
                budget, basis, status = "", "clock/source-specific bound not established by this scan", "needs_manual_bound"
            else:
                budget, basis, status = "", "no scanned timing pattern", "no_pattern_found"
            row = {"source_path": str(source_path.relative_to(ROOT)),
                   "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                   "family_root": test_root, "status": status,
                   "selected_case_budget_s": budget,
                   "selected_case_worst_legal_s": f"{WORST_CASE_S:.6f}" if rel in KNOWN else "",
                   "basis": basis}
            for name, lines in hits.items():
                row[name + "_count"] = len(lines)
                row[name + "_lines"] = ";".join(map(str, lines))
            rows.append(row)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    from collections import Counter
    by_status = Counter(row["status"] for row in rows)
    by_root = Counter(row["family_root"] for row in rows)
    lines = ["# Pinned Zephyr static timing threshold scan — 2026-10-05", "",
             "This scan reads source only; it does not run Zephyr or establish",
             "hardware-specific limits for other boards. Its exact scope is the",
             "seven pinned test trees below, including C/C++ sources and headers.",
             "Python host tests, generated files, and other Zephyr test trees are",
             "outside scope. The CSV records line candidates and SHA-256 per file.", "",
             "| Test tree | Source files |", "|---|---:|"]
    for test_root, count in sorted(by_root.items()):
        lines.append(f"| `tests/{test_root}` | {count} |")
    lines += ["", "| Review status | Files |", "|---|---:|"]
    for status, count in sorted(by_status.items()):
        lines.append(f"| {status} | {count} |")
    lines += ["", f"The three selected STM32 RTC sources have fixed observation",
              f"boundaries of 13, 13, and 14.5 host seconds, below the ideal",
              f"10-second calendar transition at the legal slow endpoint",
              f"(`{WORST_CASE_S:.6f}` host seconds). That shortfall identifies a",
              "clock-bound threshold risk, not a full behavior verdict. Every",
              "other hit remains `needs_manual_bound`; a literal timeout alone",
              "cannot be judged against an unspecified clock or API guarantee.", ""]
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {len(rows)} source rows, {dict(by_status)}")


if __name__ == "__main__":
    main()
