#!/usr/bin/env python3
"""Source-backed first-failing-assertion ledger for scored RTC offset kills."""

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/rtc_alarm_offset_v1"
ASSERTION = re.compile(r"Assertion failed at [^\r\n]*?:(\d+): ([^\r\n]+)")
MIXED = "sol-range_present-rtc_alarm_callback-r03__late"


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    summary = json.loads((OUT / "analysis_summary.json").read_text())
    rows = []
    for item in summary["rows"]:
        if item["status"] != "kill":
            continue
        suite = manifest["suites"][item["suite_id"]]
        record = json.loads((OUT / "records" / f"{item['run_id']}.json").read_text())
        uart = (ROOT / record["uart_path"]).read_text(errors="replace")
        match = ASSERTION.search(uart)
        if not match:
            raise RuntimeError(f"No first assertion in {item['run_id']}")
        trailing = uart[match.end():].splitlines()
        failure_message = next((line.strip() for line in trailing if line.strip()), "")
        line = int(match.group(1))
        source = ROOT / suite["source_path"]
        source_lines = source.read_text().splitlines()
        if not 1 <= line <= len(source_lines):
            raise RuntimeError(f"Bad source line in {item['run_id']}: {line}")
        if item["family"] == "rtc_alarm_pending":
            category = "alarm_register_readback_second"
            confirmed = True
            rationale = "Selected assertion compares alarm_get_time second with requested RTC second."
        elif item["sign"] == -1:
            category = "callback_before_requested_RTC_time"
            confirmed = True
            rationale = "First assertion rejects a callback observed while RTC calendar is before the target, or rejects its captured callback calendar time."
        elif item["run_id"] == MIXED:
            category = "combined_ID_read_or_callback_RTC_time"
            confirmed = False
            rationale = "Saved assertion combines wrong alarm ID, RTC read failure, and callback calendar mismatch; trace does not expose which branch set the flag."
        else:
            category = "callback_calendar_second_mismatch"
            confirmed = True
            rationale = "First assertion compares callback or observation RTC calendar with requested target second; a decoded bitmask identifies late calendar time where applicable."
        rows.append({"run_id": item["run_id"], "suite_id": item["suite_id"],
                     "family": item["family"], "kind": item["kind"],
                     "model": item["model"], "prompt_condition": item["prompt_condition"] or "n/a",
                     "sign": item["sign"], "category": category,
                     "calendar_relative_confirmed": confirmed,
                     "source_path": suite["source_path"], "source_sha256": suite["source_sha256"],
                     "source_line": line, "source_text": source_lines[line - 1].strip(),
                     "assertion": match.group(2).strip(), "failure_message": failure_message,
                     "rationale": rationale,
                     "record_sha256": item["record_sha256"], "uart_sha256": record["uart_sha256"]})
    if len(rows) != 73:
        raise RuntimeError(f"Expected 73 scored kills, found {len(rows)}")
    categories = Counter(row["category"] for row in rows)
    print(dict(categories))
    path = ROOT / "analysis/rtc_alarm_offset_v1_assertion_audit.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "analysis/rtc_alarm_offset_v1_assertion_audit.json").write_text(
        json.dumps({"registered_manifest_sha256": summary["manifest_sha256"],
                    "unit": "first failing assertion in each scored offset kill",
                    "method": "single-reviewer source and persisted-UART coding; combined causes retained separately",
                    "categories": dict(categories), "confirmed_calendar_relative": sum(
                        row["calendar_relative_confirmed"] for row in rows),
                    "combined_or_ambiguous": sum(not row["calendar_relative_confirmed"] for row in rows)},
                   indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
