#!/usr/bin/env python3
"""Validate Phase 2 task matches against frozen nominal upstream records."""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "subjects/phase2_tasks.json"
UPSTREAM = ROOT / "subjects/upstream/zephyr"
OUT = ROOT / "results/phase2/task_validation.json"
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    tasks = json.loads(TASKS.read_text())
    commit = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if commit != tasks["zephyr_commit"]:
        raise RuntimeError("Zephyr checkout changed")
    hsi = [json.loads(line) for line in (ROOT / "results/phase1/runs.jsonl").read_text().splitlines()]
    lsi = [json.loads(line) for line in (ROOT / "results/phase1_lsi_alarm/runs.jsonl").read_text().splitlines()]
    matches = []
    for task in tasks["tasks"]:
        app = UPSTREAM / task["human_app"]
        if not app.is_dir():
            raise RuntimeError(f"Missing upstream app: {task['id']}")
        if task["arm"] == "hsi":
            candidates = [r for r in hsi if r["subject_id"] == task["id"]
                          and r["condition"] == "nominal" and r["cpu_performance_mips"] == 16]
        else:
            candidates = [r for r in lsi if r["condition"] == "nominal" and r["variant"] == "callback"]
        if len(candidates) != 1 or candidates[0]["outcome"] != "pass":
            raise RuntimeError(f"No single nominally passing upstream run: {task['id']}")
        run = candidates[0]
        uart = ROOT / run["uart_path"]
        cases = CASE.findall(uart.read_text(errors="replace"))
        case_statuses = [status for status, case in cases if case == task["human_case"]]
        if case_statuses != ["PASS"]:
            raise RuntimeError(f"Human match is not a single passing case: {task['id']}: {case_statuses}")
        matches.append({"task_id": task["id"], "arm": task["arm"],
                        "human_case": task["human_case"], "human_app": task["human_app"],
                        "nominal_run_id": run["run_id"], "nominal_uart_sha256": sha256(uart)})
    record = {"validated_utc": datetime.now(timezone.utc).isoformat(),
              "task_manifest_sha256": sha256(TASKS), "upstream_commit": commit,
              "matches": matches}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        prior = json.loads(OUT.read_text())
        if {k: v for k, v in prior.items() if k != "validated_utc"} != {k: v for k, v in record.items() if k != "validated_utc"}:
            raise RuntimeError("Existing task match validation differs")
    else:
        OUT.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(f"validated {len(matches)} nominally passing upstream case matches")


if __name__ == "__main__":
    main()
