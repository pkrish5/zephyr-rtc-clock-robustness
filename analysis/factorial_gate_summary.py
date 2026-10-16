#!/usr/bin/env python3
"""Report original/amended factorial attrition without invoking varied schedules."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/spec_context_factorial_v1"
RESULTS = ROOT / "results/spec_context_factorial_v1"
REVIEW = ROOT / "analysis/factorial_source_decisions.json"
TIMING_TO_RQ1 = {"inadequate": "unjustified", "no_issue_found": "none_found",
                 "unknown": "unknown", "not_evaluable": "unknown", "pending": "pending"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_for(run_id):
    retry = RESULTS / "build_retry_records" / f"{run_id}.json"
    path = retry if retry.exists() else RESULTS / "build_records" / f"{run_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    order = json.loads((BASE / "call_order.json").read_text())["calls"]
    review = json.loads(REVIEW.read_text())["decisions"] if REVIEW.exists() else {}
    rows = []
    for call in order:
        model = call["model"].removeprefix("gpt-6-")
        run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
        directory = BASE / "suites" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
        metadata = directory / "metadata.json"
        generation = json.loads(metadata.read_text()) if metadata.exists() else None
        build = build_for(run_id)
        if generation and build and build["source_sha256"] != generation["source_sha256"]:
            raise ValueError(f"Build/source mismatch: {run_id}")
        source_review = review.get(run_id)
        if source_review and generation and source_review["source_sha256"] != generation["source_sha256"]:
            raise ValueError(f"Review/source mismatch: {run_id}")
        nominal = []
        for repeat in range(5):
            path = RESULTS / "nominal_records" / f"{run_id}-nominal-{repeat:03d}.json"
            if path.exists():
                record = json.loads(path.read_text())
                if not build or record["elf_sha256"] != build["elf_sha256"]:
                    raise ValueError(f"Nominal/ELF mismatch: {run_id} repeat {repeat}")
                nominal.append(record["outcome"])
            else:
                nominal.append("missing")
        functional = source_review["functional"] if source_review else "pending"
        timing = source_review["timing_bound"] if source_review else "pending"
        nominal_screened = all(value != "missing" for value in nominal)
        nominal_5of5 = nominal_screened and all(value == "pass" for value in nominal)
        build_pass = bool(build and build["status"] == "pass")
        rows.append({
            "run_id": run_id, "call_index": call["call_index"],
            "model": model, "condition": call["condition"], "task_id": call["task_id"],
            "generation": generation["status"] if generation else "pending",
            "source_sha256": generation["source_sha256"] if generation else None,
            "build": build["status"] if build else "not_run",
            "elf_sha256": build["elf_sha256"] if build else None,
            "first_nominal": nominal[0], "nominal_repeats": nominal,
            "nominal_5of5_screened": nominal_screened,
            "nominal_5of5_status": "pass" if nominal_5of5 else
                                    ("fail" if nominal_screened else "not_screened"),
            "fresh_nominal_5of5": nominal_5of5,
            "functional": functional, "timing_bound": timing,
            "rq1_source_status": TIMING_TO_RQ1[timing],
            "original_strict_eligible": build_pass and nominal_5of5 and functional == "met" and timing == "no_issue_found",
            "amended_functional_eligible": build_pass and nominal_5of5 and functional == "met",
        })
    if args.require_complete and any(
            row["generation"] == "pending" or
            (row["generation"] == "generated" and
             (row["build"] == "not_run" or row["functional"] == "pending" or
              row["timing_bound"] == "pending" or
              (row["build"] == "pass" and row["first_nominal"] == "missing") or
              (row["build"] == "pass" and row["functional"] == "met" and
               "missing" in row["nominal_repeats"])))
            for row in rows):
        raise ValueError("Generation, build, nominal, or source gates remain pending")
    cells = defaultdict(list)
    for row in rows:
        cells[(row["model"], row["condition"])].append(row)
    cell_summary = {}
    for (model, condition), group in sorted(cells.items()):
        key = f"{model}/{condition}"
        cell_summary[key] = {
            "planned": len(group),
            "generation": dict(Counter(row["generation"] for row in group)),
            "build": dict(Counter(row["build"] for row in group)),
            "first_nominal": dict(Counter(row["first_nominal"] for row in group)),
            "nominal_5of5_screened": sum(row["nominal_5of5_screened"] for row in group),
            "fresh_nominal_5of5": sum(row["fresh_nominal_5of5"] for row in group),
            "functional": dict(Counter(row["functional"] for row in group)),
            "timing_bound": dict(Counter(row["timing_bound"] for row in group)),
            "original_strict_eligible": sum(row["original_strict_eligible"] for row in group),
            "amended_functional_eligible": sum(row["amended_functional_eligible"] for row in group),
        }
    output = {"planned": len(rows), "completed": all(row["generation"] != "pending" for row in rows),
              "call_order_sha256": sha(BASE / "call_order.json"),
              "source_review_sha256": sha(REVIEW) if REVIEW.exists() else None,
              "cells": cell_summary, "rows": rows,
              "source_gate_note": "Original strict = functional met and timing no issue found; amended = functional met. Both additionally require build pass and fresh nominal 5/5. Timing unknown is excluded from strict but included in amended when functional is met. Unscreened five-repeat outcomes are missing, not failures."}
    path = RESULTS / "gate_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Factorial gates: {sum(row['generation']!='pending' for row in rows)}/390 generated; "
          f"{sum(row['build']=='pass' for row in rows)} builds; "
          f"{sum(row['fresh_nominal_5of5'] for row in rows)}/"
          f"{sum(row['nominal_5of5_screened'] for row in rows)} 5/5 passes/screens; "
          f"{sum(row['functional']!='pending' for row in rows)} source reviews")


if __name__ == "__main__":
    main()
