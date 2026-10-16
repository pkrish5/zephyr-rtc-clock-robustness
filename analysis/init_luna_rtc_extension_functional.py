#!/usr/bin/env python3
"""Freeze split-gate functional source judgments before timing perturbation."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/luna_rtc_extension_functional_decisions.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise ValueError("Functional decisions already frozen")
    rows = {}
    for task in ("rtc_time_counting", "rtc_alarm_pending"):
        for i in range(1, 6):
            run_id = f"{task}-r{i:02d}"
            source = ROOT / "generated/luna_rtc_extension/suites" / task / f"r{i:02d}/test.c"
            metadata = json.loads((source.parent / "metadata.json").read_text())
            if sha(source) != metadata["source_sha256"]:
                raise ValueError(f"Frozen source changed: {run_id}")
            if task == "rtc_alarm_pending":
                status = "not_evaluable"
                evidence = ("Frozen suite fails compilation at the pinned RTC API signatures; "
                            "no intended alarm assertion is executable.")
            elif i == 5:
                status = "not_met"
                evidence = ("The test compares every poll only to the initial RTC time; "
                            "the assigned previous value is never asserted, so a later "
                            "calendar regression can pass the monotonicity oracle.")
            else:
                status = "met"
                evidence = ("The compiled source asserts successful set/read, consecutive "
                            "calendar monotonicity, and arrival at the +10-second target "
                            "across the year boundary. The observation deadline is judged "
                            "separately as a timing-bound outcome.")
            rows[run_id] = {
                "task_id": task, "source_path": str(source.relative_to(ROOT)),
                "source_sha256": metadata["source_sha256"],
                "functional": status, "evidence": evidence,
                "reviewer": "Codex source review before RTC-extension timing perturbation",
            }
    OUTPUT.write_text(json.dumps({
        "schema_version": 1,
        "reviewed_utc": datetime.now(timezone.utc).isoformat(),
        "split_protocol_sha256": sha(ROOT / "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md"),
        "decisions": rows,
    }, sort_keys=True, indent=2) + "\n")
    print("Frozen amended functional judgments for ten Luna RTC-extension sources")


if __name__ == "__main__":
    main()
