#!/usr/bin/env python3
"""Initialize and audit pre-variation source review of Stage B callback outputs."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/stage_b_callback_v1"
LEDGER = ROOT / "analysis/stage_b_callback_source_review.json"
FUNCTIONAL = {"met", "not_met", "unknown", "pending"}
TIMING = {"inadequate", "no_issue_found", "unknown", "pending"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected():
    rows = {}
    for call in json.loads((BASE / "call_order.json").read_text())["calls"]:
        model = call["model"].removeprefix("gpt-6-")
        rid = f"{model}-{call['condition']}-rtc_alarm_callback-r{call['sample_index']:02d}"
        directory = BASE / "suites" / model / call["condition"] / f"r{call['sample_index']:02d}"
        metadata = directory / "metadata.json"
        if not metadata.exists():
            continue
        generation = json.loads(metadata.read_text())
        if generation["status"] != "generated":
            continue
        source = directory / "test.c"
        if sha(source) != generation["source_sha256"]:
            raise ValueError(f"Frozen source changed: {rid}")
        rows[rid] = {
            "run_id": rid, "call_index": call["call_index"],
            "model": call["model"], "condition": call["condition"],
            "task_id": call["task_id"],
            "source_path": str(source.relative_to(ROOT)),
            "source_sha256": sha(source),
            "contract": "loose_callback" if call["condition"] == "loose_spec" else "original_precise_callback",
        }
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    current = expected()
    saved = json.loads(LEDGER.read_text()) if LEDGER.exists() else {
        "schema_version": 1,
        "review_timing": "Before Stage B legal-clock and fault outcomes",
        "reviewer": "Single unblinded automated source reviewer",
        "decisions": {},
    }
    added = 0
    for rid, base in current.items():
        if rid not in saved["decisions"]:
            if not args.init:
                raise ValueError(f"Source pending ledger initialization: {rid}")
            saved["decisions"][rid] = {
                **base,
                "functional": "pending", "functional_evidence": "",
                "timing_bound": "pending", "timing_evidence": "",
                "exact_calendar_oracle": "pending", "alarm_readback": "pending",
                "reviewed_utc": None,
            }
            added += 1
        row = saved["decisions"][rid]
        for key, value in base.items():
            if row[key] != value:
                raise ValueError(f"Frozen review input changed: {rid}.{key}")
        if row["functional"] not in FUNCTIONAL or row["timing_bound"] not in TIMING:
            raise ValueError(f"Invalid source judgment: {rid}")
        if row["functional"] != "pending" and not row["functional_evidence"].strip():
            raise ValueError(f"Missing functional evidence: {rid}")
        if row["timing_bound"] != "pending" and not row["timing_evidence"].strip():
            raise ValueError(f"Missing timing evidence: {rid}")
    if set(saved["decisions"]) != set(current):
        raise ValueError("Finalized source disappeared")
    if args.init and (added or not LEDGER.exists()):
        LEDGER.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n")
    print(f"Reviewed source inventory {len(current)}, new {added}, functional {dict(Counter(x['functional'] for x in saved['decisions'].values()))}")


if __name__ == "__main__":
    main()
