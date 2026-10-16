#!/usr/bin/env python3
"""Maintain a complete four-way ledger for observed RTC flips and endpoints."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/phase3_rtc"
DECISIONS = ROOT / "analysis/phase3_rtc_classification_decisions.json"
VALID = {"pending", "brittle_test_assumption", "firmware_race_or_bug",
         "simulator_or_peripheral_artifact", "unknown"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    plan = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())
    expected = {}
    for path in (RESULTS / "records").glob("*.json"):
        run = json.loads(path.read_text())
        if run["condition"] not in ("seeded", "min", "max") or run["outcome"] != "fail":
            continue
        ident = run["version_id"]
        nominal = [RESULTS / "records" / f"{ident}-nominal-{i:03d}.json"
                   for i in range(plan["nominal_repeats"])]
        if not all(p.exists() and json.loads(p.read_text())["outcome"] == "pass" for p in nominal):
            continue
        expected[run["run_id"]] = {
            "version_id": ident, "seed": run["seed"],
            "condition": run["condition"],
            "lsi_frequency_hz": run["lsi_frequency_hz"],
            "run_record_path": str(path.relative_to(ROOT)),
            "run_record_sha256": sha256(path),
            "uart_path": run["uart_path"], "uart_sha256": run["uart_sha256"],
            "trace_path": run["trace_path"], "trace_sha256": run["trace_sha256"],
            "replay_record_path": None,
            "replay_identical": None,
            "classification": "pending", "evidence": "", "reviewer": "",
        }
    saved = json.loads(DECISIONS.read_text()) if DECISIONS.exists() else {
        "schema_version": 1,
        "plan_sha256": sha256(ROOT / "subjects/phase3_rtc/plan.json"),
        "decision_procedure": "paper/DESIGN.md#flip-decision-procedure",
        "note": "Exactly one category per observed pass-to-fail flip, including endpoints outside the seeded-rate denominator; pending is incomplete, not dropped.",
        "decisions": {},
    }
    if saved["plan_sha256"] != sha256(ROOT / "subjects/phase3_rtc/plan.json"):
        raise ValueError("Plan changed since classification ledger was created")
    if set(saved["decisions"]) - set(expected):
        raise ValueError("Previously observed flip disappeared")
    added = 0
    upgraded = 0
    for run_id, fresh in expected.items():
        if run_id not in saved["decisions"]:
            if not args.init:
                raise ValueError(f"Missing flip decision: {run_id}; use --init")
            saved["decisions"][run_id] = fresh
            added += 1
        row = saved["decisions"][run_id]
        # Older seeded decisions preceded endpoint registration in this ledger.
        if "condition" not in row and row["seed"] is not None:
            row["condition"] = "seeded"
            upgraded += 1
        for field in ("version_id", "seed", "lsi_frequency_hz", "run_record_path",
                      "condition", "run_record_sha256", "uart_path", "uart_sha256",
                      "trace_path", "trace_sha256"):
            if row[field] != fresh[field]:
                raise ValueError(f"Frozen flip evidence changed: {run_id}: {field}")
        if row["classification"] not in VALID:
            raise ValueError(f"Invalid flip category: {run_id}")
        if row["classification"] != "pending":
            if not row["evidence"].strip() or not row["reviewer"].strip():
                raise ValueError(f"Classification lacks evidence: {run_id}")
            if not row["replay_record_path"]:
                raise ValueError(f"Classification lacks replay: {run_id}")
            replay_path = ROOT / row["replay_record_path"]
            if not replay_path.exists():
                raise ValueError(f"Replay record missing: {run_id}")
            replay = json.loads(replay_path.read_text())
            if row["replay_identical"] != replay["identical_trace_and_verdict"]:
                raise ValueError(f"Replay status mismatch: {run_id}")
            if not row["replay_identical"] and row["classification"] != "unknown":
                raise ValueError(f"Divergent replay must be unknown: {run_id}")
    if args.init and (added or upgraded):
        DECISIONS.write_text(json.dumps(saved, sort_keys=True, indent=2) + "\n")
    counts = {kind: sum(x["classification"] == kind for x in saved["decisions"].values())
              for kind in sorted(VALID)}
    print(f"RTC flips: observed={len(expected)}, categories={counts}, newly registered={added}")


if __name__ == "__main__":
    main()
