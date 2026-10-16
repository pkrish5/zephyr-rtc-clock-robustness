#!/usr/bin/env python3
"""Source-only wait inventory and saved nominal-runtime table for RTC cases.

This script does not build firmware or launch a simulator. Labels are syntactic
descriptions, not judgments that a particular wait is adequate.
"""

import csv
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
NOMINAL = ROOT / "results/spec_context_factorial_v1/nominal_records"
OUT = ROOT / "analysis/rtc_static_waits.csv"
FAMILIES = {"rtc_alarm_callback", "rtc_time_counting", "rtc_alarm_pending"}
HUMAN = {
    "rtc_alarm_callback": "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c",
    "rtc_time_counting": "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_time_incrementing.c",
    "rtc_alarm_pending": "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm.c",
}
HUMAN_NOMINAL = {
    "rtc_alarm_callback": ("results/phase3_rtc/records", "upstream-nominal-*.json"),
    "rtc_time_counting": ("results/rtc_counting/nominal_records", "counting-nominal-s2-*.json"),
    "rtc_alarm_pending": ("results/rtc_alarm_pending/nominal_records", "alarm_pending-nominal-*.json"),
}


def styles(source):
    patterns = {
        "fixed_sleep": r"\bk_(?:msleep|usleep|sleep|busy_wait)\s*\(",
        "event_wait": r"\bk_(?:sem_take|poll|event_wait|msgq_get|fifo_get)\s*\(",
        "calendar_poll": r"\brtc_get_time\s*\(",
        "pending_poll": r"\brtc_alarm_is_pending\s*\(",
        "callback": r"\brtc_alarm_set_callback\s*\(",
        "host_deadline": r"\bk_(?:uptime_get|cycle_get_32|cycle_get_64)\s*\(",
    }
    return {name: bool(re.search(pattern, source)) for name, pattern in patterns.items()}


def nominal_times(run_id):
    vals = []
    for path in NOMINAL.glob(f"{run_id}-nominal-*.json"):
        record = json.loads(path.read_text())
        if record.get("outcome") == "pass" and record.get("wall_seconds") is not None:
            vals.append(record["wall_seconds"])
    return vals


def human_nominal_times(family):
    directory, pattern = HUMAN_NOMINAL[family]
    vals = []
    for path in (ROOT / directory).glob(pattern):
        record = json.loads(path.read_text())
        if record.get("outcome") == "pass" and record.get("wall_seconds") is not None:
            vals.append(record["wall_seconds"])
    return vals


def main():
    gate = json.loads(GATE.read_text())
    rows = []
    for item in gate["rows"]:
        if item["task_id"] not in FAMILIES or not item["amended_functional_eligible"]:
            continue
        suite = item["run_id"]
        source_path = next((ROOT / "generated/spec_context_factorial_v1/suites").rglob(f"{suite}/test.c"), None)
        if source_path is None:
            parts = [item["model"], item["condition"], item["task_id"], suite.rsplit("-", 1)[-1]]
            source_path = ROOT / "generated/spec_context_factorial_v1/suites" / Path(*parts) / "test.c"
        source = source_path.read_text()
        times = nominal_times(suite)
        row = {"suite_id": suite, "kind": "ai", "model": item["model"],
               "prompt_condition": item["condition"], "task_family": item["task_id"],
               "source_path": str(source_path.relative_to(ROOT)),
               "nominal_pass_records": len(times),
               "nominal_wall_median_s": round(statistics.median(times), 3) if times else "",
               "nominal_wall_min_s": round(min(times), 3) if times else "",
               "nominal_wall_max_s": round(max(times), 3) if times else ""}
        row.update(styles(source))
        rows.append(row)
    for family, rel in HUMAN.items():
        times = human_nominal_times(family)
        row = {"suite_id": f"human-{family}", "kind": "human", "model": "human",
               "prompt_condition": "none", "task_family": family, "source_path": rel,
               "nominal_pass_records": len(times),
               "nominal_wall_median_s": round(statistics.median(times), 3) if times else "",
               "nominal_wall_min_s": round(min(times), 3) if times else "",
               "nominal_wall_max_s": round(max(times), 3) if times else ""}
        row.update(styles((ROOT / rel).read_text()))
        rows.append(row)
    rows.sort(key=lambda row: row["suite_id"])
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} RTC source rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
