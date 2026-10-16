#!/usr/bin/env python3
"""Initialize/audit source-only functional and timing reviews before varied runs."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/spec_context_factorial_v1"
LEDGER = ROOT / "analysis/factorial_source_decisions.json"
TASKS = {task["id"]: task for task in json.loads((ROOT / "subjects/phase2_tasks_v2.json").read_text())["tasks"]}
FUNCTIONAL = {"met", "not_met", "unknown", "not_evaluable", "pending"}
TIMING = {"inadequate", "no_issue_found", "unknown", "not_evaluable", "pending"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected():
    rows = {}
    for call in json.loads((BASE / "call_order.json").read_text())["calls"]:
        model = call["model"].removeprefix("gpt-6-")
        run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
        directory = BASE / "suites" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
        metadata = directory / "metadata.json"
        if not metadata.exists():
            continue
        generation = json.loads(metadata.read_text())
        if generation["status"] != "generated":
            continue
        source = directory / "test.c"
        if sha(source) != generation["source_sha256"]:
            raise ValueError(f"Frozen source mismatch: {run_id}")
        rows[run_id] = {
            "run_id": run_id, "call_index": call["call_index"],
            "model": call["model"], "condition": call["condition"],
            "task_id": call["task_id"], "source_path": str(source.relative_to(ROOT)),
            "source_sha256": sha(source),
            "required_oracles": TASKS[call["task_id"]]["required_oracles"],
        }
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    current = expected()
    saved = json.loads(LEDGER.read_text()) if LEDGER.exists() else {
        "schema_version": 1, "review_timing": "Before new factorial varied schedules",
        "reviewer": "Codex source reviewer; model/condition metadata visible",
        "decisions": {},
    }
    added = 0
    for run_id, base in current.items():
        if run_id not in saved["decisions"]:
            if not args.init:
                raise ValueError(f"Source pending ledger initialization: {run_id}")
            saved["decisions"][run_id] = {
                **base, "feature_path": "pending", "feature_path_evidence": "",
                "functional": "pending", "functional_evidence": "",
                "timing_bound": "pending", "timing_evidence": "",
                "reviewed_utc": None,
            }
            added += 1
        row = saved["decisions"][run_id]
        for key, value in base.items():
            if row[key] != value:
                raise ValueError(f"Frozen review input changed: {run_id}.{key}")
        if row["functional"] not in FUNCTIONAL or row["timing_bound"] not in TIMING:
            raise ValueError(f"Invalid source judgment: {run_id}")
        if row["functional"] != "pending" and not row["functional_evidence"].strip():
            raise ValueError(f"Missing functional evidence: {run_id}")
        if row["timing_bound"] != "pending" and not row["timing_evidence"].strip():
            raise ValueError(f"Missing timing evidence: {run_id}")
    if set(saved["decisions"]) != set(current):
        raise ValueError("Finalized source disappeared")
    if args.init and (added or not LEDGER.exists()):
        LEDGER.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n")
    functional = Counter(row["functional"] for row in saved["decisions"].values())
    timing = Counter(row["timing_bound"] for row in saved["decisions"].values())
    print(f"Review ledger: {len(current)} sources, {added} added; functional={dict(functional)}; timing={dict(timing)}")


if __name__ == "__main__":
    main()
