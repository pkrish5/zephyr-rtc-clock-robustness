#!/usr/bin/env python3
"""Create and audit a pre-perturbation, human-reviewed oracle checklist."""

import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = os.environ.get("PHASE2_COHORT", "luna_primary")
COHORT_PATHS = {
    "sol_pilot": ("subjects/phase2_tasks.json", "phase2"),
    "luna_primary": ("subjects/phase2_tasks.json", "phase2_luna"),
    "rtc_bound_supplement": ("subjects/phase2_rtc_bound_tasks.json", "phase2_rtc_bound"),
    "luna_rtc_extension": ("subjects/rtc_extension_tasks.json", "luna_rtc_extension"),
    "sol_comparison": ("subjects/phase2_tasks_v2.json", "phase2_sol_comparison"),
    "astra_comparison": ("subjects/phase2_tasks_v2.json", "phase2_astra_comparison"),
}
if COHORT not in COHORT_PATHS:
    raise ValueError("Unknown cohort")
task_file, cohort_directory = COHORT_PATHS[COHORT]
SUITES = ROOT / "generated" / cohort_directory / "suites"
OUTPUT = ROOT / "analysis" / f"phase2_oracle_decisions_{COHORT}.json"
TASKS = json.loads((ROOT / task_file).read_text())["tasks"]
VALID = {"met", "not_met", "uncertain", "pending"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected() -> dict:
    records = {}
    for task in TASKS:
        for index in range(1, 6):
            run_id = f"{task['id']}-r{index:02d}"
            source = SUITES / task["id"] / f"r{index:02d}" / "test.c"
            if not source.exists():
                continue
            metadata = json.loads((source.parent / "metadata.json").read_text())
            if sha256(source) != metadata["source_sha256"]:
                raise ValueError(f"Frozen source changed: {run_id}")
            records[run_id] = {
                "source_path": str(source.relative_to(ROOT)),
                "source_sha256": metadata["source_sha256"],
                "human_case": task["human_case"],
                "feature_path_exercised": "pending",
                "feature_path_evidence": "",
                "oracles": [
                    {"requirement": requirement, "judgment": "pending", "evidence": ""}
                    for requirement in task["required_oracles"]
                ],
                "reviewer": "",
                "reviewed_utc": None,
            }
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Add newly frozen suites as pending reviews")
    args = parser.parse_args()
    current = expected()
    saved = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {
        "schema_version": 1,
        "cohort": COHORT,
        "status_note": "Manual source review before Phase 3 timing outcomes; pending is not adequate.",
        "decisions": {},
    }
    if saved["cohort"] != COHORT or saved["schema_version"] != 1:
        raise ValueError("Review schema or cohort changed")
    if set(saved["decisions"]) - set(current):
        raise ValueError("Reviewed suite disappeared")
    added = 0
    for run_id, expected_row in current.items():
        if run_id not in saved["decisions"]:
            if not args.init:
                raise ValueError(f"Missing review record: {run_id}; run --init")
            saved["decisions"][run_id] = expected_row
            added += 1
        actual = saved["decisions"][run_id]
        for key in ("source_path", "source_sha256", "human_case"):
            if actual[key] != expected_row[key]:
                raise ValueError(f"Frozen review input changed: {run_id}.{key}")
        if [o["requirement"] for o in actual["oracles"]] != [o["requirement"] for o in expected_row["oracles"]]:
            raise ValueError(f"Oracle requirements changed: {run_id}")
        if actual["feature_path_exercised"] not in VALID:
            raise ValueError(f"Invalid path judgment: {run_id}")
        for oracle in actual["oracles"]:
            if oracle["judgment"] not in VALID:
                raise ValueError(f"Invalid oracle judgment: {run_id}")
            if oracle["judgment"] != "pending" and not oracle["evidence"].strip():
                raise ValueError(f"Missing oracle evidence: {run_id}")
        if actual["feature_path_exercised"] != "pending" and not actual["feature_path_evidence"].strip():
            raise ValueError(f"Missing feature-path evidence: {run_id}")
        if (actual["feature_path_exercised"] != "pending" or
                any(o["judgment"] != "pending" for o in actual["oracles"])) and not actual["reviewer"].strip():
            raise ValueError(f"Missing reviewer: {run_id}")
    if args.init and added:
        OUTPUT.write_text(json.dumps(saved, sort_keys=True, indent=2) + "\n")
    complete = sum(row["feature_path_exercised"] != "pending" and
                   all(o["judgment"] != "pending" for o in row["oracles"])
                   for row in saved["decisions"].values())
    adequate = sum(row["feature_path_exercised"] == "met" and
                   all(o["judgment"] == "met" for o in row["oracles"])
                   for row in saved["decisions"].values())
    print(f"{COHORT}: {len(saved['decisions'])} generated sources, {complete} fully reviewed, "
          f"{adequate} source-oracle adequate, {added} added")


if __name__ == "__main__":
    main()
