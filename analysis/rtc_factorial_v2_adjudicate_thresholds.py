#!/usr/bin/env python3
"""Incremental source-backed adjudication of observed threshold failures."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_factorial_v2"
OUT = ROOT / "analysis/rtc_factorial_v2_classification.json"
CASES = {
    "astra-range_absent-rtc_alarm_pending-r05": (15, "test.c:101", "No pending alarm at/after target within 15 seconds", "generated/spec_context_factorial_v1/suites/astra/range_absent/rtc_alarm_pending/r05/test.c", 101),
    "sol-range_absent-rtc_alarm_pending-r03": (15, "test.c:82", "RTC did not reach alarm time", "generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c", 82),
    "sol-range_absent-rtc_alarm_pending-r01": (16, "test.c:80", "alarm not pending within 16 seconds", "generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r01/test.c", 80),
    "human-rtc_alarm_callback": (13, "test_alarm_callback.c:140", "Alarm 0 callback should have been called", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c", 140),
    "human-rtc_alarm_pending": (13, "test_alarm.c:203", "Alarm 0 should be pending", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm.c", 203),
    "human-rtc_time_counting": (14.5, "test_time_incrementing.c:58", "Timeout occurred waiting for time to increment", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_time_incrementing.c", 58),
}
TRACE_KEYS = ("lsi_frequency_hz", "observations", "cases", "outcome", "error")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((BASE / "manifest.json").read_text())
    previous = json.loads(OUT.read_text()) if OUT.exists() else {"rows": []}
    by_id = {x["run_id"]: x for x in previous["rows"]}
    added = 0
    for record_path in sorted((BASE / "records").glob("*.json")):
        original = json.loads(record_path.read_text())
        rid, run_id = original["suite_id"], original["run_id"]
        if rid not in CASES or original["outcome"] != "fail" or run_id in by_id:
            continue
        replay_path = BASE / "replay_records" / f"{run_id}.json"
        if not replay_path.exists():
            continue
        replay = json.loads(replay_path.read_text())
        first = json.loads((ROOT / original["trace_path"]).read_text())
        second = json.loads((ROOT / replay["trace_path"]).read_text())
        if replay["outcome"] != "fail" or not all(first[k] == second[k] for k in TRACE_KEYS):
            continue
        budget, location, message, source, line = CASES[rid]
        hz = original["lsi_frequency_hz"]
        arrival = 320000 / hz
        if arrival <= budget:
            continue
        uart = (ROOT / original["uart_path"]).read_text(errors="replace")
        if location not in uart or message not in uart:
            continue
        if original["condition"] == "seeded" and manifest["versions"][rid]["role"] == "sampled_predictable":
            if original["seed"] not in manifest["versions"][rid]["predicted_failure_seeds"]:
                continue
        source_path = ROOT / source
        if digest(source_path) != manifest["versions"][rid]["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {rid}")
        if rid == "human-rtc_time_counting":
            basis = (f"Frozen upstream test takes at most 30 calendar polls spaced by 500 ms; its last poll occurs at about 14.5 host seconds. At legal LSI {hz} Hz and fixed 128x250 prescaler, ten RTC seconds require {arrival:.6f} host seconds, after the last poll. Original and fresh-process replay fail at the poll-limit assertion with identical saved trace fields.")
        else:
            basis = (f"Frozen test requires a 10-RTC-second alarm before a {budget}-second wall-clock deadline. At legal LSI {hz} Hz and fixed 128x250 prescaler, ideal arrival is {arrival:.6f} host seconds, after the deadline. Original and fresh-process replay fail at the same assertion with identical saved trace fields.")
        by_id[run_id] = {
            "run_id": run_id, "classification": "brittle_test_assumption",
            "basis": basis,
            "source_path": str(source_path.relative_to(ROOT)), "source_line": line,
            "assertion_message": message, "lsi_frequency_hz": hz,
            "calculated_earliest_alarm_host_seconds": arrival,
            "original_record_sha256": digest(record_path),
            "replay_record_sha256": digest(replay_path),
            "persisted_replay_identical": True,
            "adjudicated_utc": datetime.now(timezone.utc).isoformat(),
        }
        added += 1
    original_paths = list((BASE / "records").glob("*.json"))
    all_failed_ids = {
        json.loads(path.read_text())["run_id"] for path in original_paths
        if json.loads(path.read_text())["outcome"] == "fail"
    }
    complete = (len(original_paths) == 102 * len(manifest["versions"])
                and all_failed_ids == set(by_id)
                and not (BASE / "STOP_PREDICTION_MISMATCH.json").exists())
    output = {"schema_version": 1,
              "status": "complete_source_backed" if complete else "partial_while_arm_running",
              "rows": [by_id[k] for k in sorted(by_id)]}
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Adjudicated {added} new threshold failures; total {len(by_id)}")


if __name__ == "__main__":
    main()
