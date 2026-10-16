#!/usr/bin/env python3
"""Audit immutable RTC alarm-offset originals and produce derived score tables."""

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/rtc_alarm_offset_v1"
PATTERN = re.compile(
    r"QUALITY_ALARM_OFFSET id=(\d+) sign=(-?\d+) requested=(-?\d+):(-?\d+):(-?\d+) "
    r"programmed=(-?\d+):(-?\d+):(-?\d+) mask=(\d+)")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = OUT / "manifest.json"
    m = read(manifest_path)
    activation = read(OUT / "activation_audit.json")
    if activation["status"] != "validated" or activation["manifest_sha256"] != sha(manifest_path):
        raise RuntimeError("Reference activation gate is absent or invalid")
    rows = []
    missing_files = []
    for rid, suite in sorted(m["suites"].items()):
        if suite["kind"] == "reference":
            continue
        for sign, name in ((-1, "early"), (1, "late")):
            label = f"{rid}__{name}"
            path = OUT / "records" / f"{label}.json"
            if not path.exists():
                missing_files.append(label)
                continue
            record = read(path)
            uart = ROOT / record["uart_path"]
            trace = ROOT / record["trace_path"]
            elf = OUT / "builds" / label / "build/zephyr/zephyr.elf"
            if record["manifest_sha256"] != sha(manifest_path):
                raise RuntimeError(f"Manifest hash mismatch: {label}")
            for file, field in ((uart, "uart_sha256"), (trace, "trace_sha256"),
                                (elf, "elf_sha256")):
                if not file.exists() and record[field] is None and record["outcome"] == "harness_error":
                    continue
                if not file.exists() or sha(file) != record[field]:
                    raise RuntimeError(f"Saved artifact hash mismatch: {label}: {file}")
            if record["source_sha256"] != suite["source_sha256"]:
                raise RuntimeError(f"Source hash mismatch: {label}")
            text = uart.read_text(errors="replace") if uart.exists() else ""
            logs = PATTERN.findall(text)
            for entry in logs:
                requested = sum(int(value) * factor for value, factor in
                                zip(entry[2:5], (3600, 60, 1)))
                programmed = sum(int(value) * factor for value, factor in
                                 zip(entry[5:8], (3600, 60, 1)))
                if int(entry[8]) == 7 and (programmed - requested) % 86400 != sign % 86400:
                    raise RuntimeError(f"Programmed RTC-second offset mismatch: {label}")
            valid_logs = [entry for entry in logs if int(entry[1]) == sign]
            alarm = suite["family"] != "rtc_time_counting"
            if not alarm:
                status = "control_pass" if record["outcome"] == "pass" and not logs else (
                    "control_error" if record["outcome"] in ("harness_error", "timeout", "unknown") else
                    "control_unexpected")
            elif record["outcome"] in ("harness_error", "timeout", "unknown"):
                status = "missing_verdict"
            elif not valid_logs:
                status = "inactive"
            elif record["outcome"] == "fail" and any(
                    case["status"] == "fail" and
                    (not suite.get("selected_case") or case["case"] == suite["selected_case"])
                    for case in record["cases"]):
                status = "kill"
            elif record["outcome"] == "pass":
                status = "survive"
            else:
                status = "ambiguous"
            replay_path = OUT / "replays/records" / f"{label}__replay.json"
            replay = read(replay_path) if replay_path.exists() else None
            replay_match = None
            if replay is not None:
                replay_uart = (ROOT / replay["uart_path"]).read_text(errors="replace")
                replay_match = (
                    replay["outcome"] == record["outcome"] and
                    replay["cases"] == record["cases"] and
                    replay["error"] == record["error"] and
                    PATTERN.findall(replay_uart) == logs)
            rows.append({"run_id": label, "suite_id": rid, "family": suite["family"],
                         "kind": suite["kind"], "model": suite["model"],
                         "prompt_condition": suite.get("prompt_condition"),
                         "sign": sign, "status": status, "outcome": record["outcome"],
                         "activation_logs": len(valid_logs), "replay_match": replay_match,
                         "record_sha256": sha(path)})
    by_cell = defaultdict(lambda: defaultdict(int))
    by_task = defaultdict(lambda: defaultdict(int))
    for row in rows:
        by_cell[(row["model"], row["prompt_condition"], row["sign"])][row["status"]] += 1
        by_task[(row["family"], row["kind"], row["sign"])][row["status"]] += 1
    summary = {"manifest_sha256": sha(manifest_path), "expected_records": 138,
               "found_records": len(rows), "missing_files": missing_files,
               "status_counts": dict((s, sum(r["status"] == s for r in rows))
                                     for s in sorted({r["status"] for r in rows})),
               "cells": [{"model": model, "prompt_condition": condition, "sign": sign,
                          **counts} for (model, condition, sign), counts in sorted(
                              by_cell.items(), key=lambda x: str(x[0]))],
               "tasks": [{"family": family, "kind": kind, "sign": sign, **counts}
                         for (family, kind, sign), counts in sorted(by_task.items())],
               "rows": rows}
    target = OUT / "analysis_summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"{len(rows)}/138 originals; missing files={len(missing_files)}")
    print("statuses:", summary["status_counts"])
    for cell in summary["cells"]:
        if cell.get("kill", 0) or cell.get("survive", 0) or cell.get("missing_verdict", 0):
            print(cell)


if __name__ == "__main__":
    main()
