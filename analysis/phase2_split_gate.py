#!/usr/bin/env python3
"""Preserve and re-report the original and amended Phase 2 oracle gates."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "analysis/phase2_split_gate_decisions.json"
PROTOCOL = ROOT / "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md"
RQ1 = ROOT / "analysis/phase3_rq1_decisions.json"
COHORTS = {
    "luna_primary": ("phase2_luna", "analysis/phase2_oracle_decisions_luna_primary.json"),
    "rtc_bound_supplement": ("phase2_rtc_bound", "analysis/phase2_oracle_decisions_rtc_bound_supplement.json"),
}
FUNCTIONAL = {"met", "not_met", "unknown", "not_evaluable"}
TIMING = {"inadequate", "no_issue_found", "unknown", "not_evaluable"}
MAP_RQ1 = {"unjustified": "inadequate", "none_found": "no_issue_found",
           "unknown": "unknown"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_rows() -> dict:
    rq1 = json.loads(RQ1.read_text())["decisions"]
    rows = {}
    for cohort, (result_dir, old_review_path) in COHORTS.items():
        summary = json.loads((ROOT / "results" / result_dir / "summary.json").read_text())
        old = json.loads((ROOT / old_review_path).read_text())["decisions"]
        for task in summary["rows"]:
            for run in task["runs"]:
                run_id = run["run_id"]
                original = old[run_id]
                if cohort == "luna_primary":
                    timing_status = MAP_RQ1[rq1[run_id]["status"]]
                    timing_evidence = ("Mapped from the dated RQ1 source review: " +
                                       rq1[run_id]["evidence"])
                else:
                    timing_status = "unknown"
                    timing_evidence = "Separate RTC supplement source; timing premise needs review."
                if run["build"] != "pass" or run["nominal"] != "pass":
                    functional_status = "not_evaluable"
                    functional_evidence = (f"Build={run['build']}; original nominal={run['nominal']}. "
                                           "No executable passing functional observation is available.")
                elif run["oracle"] == "adequate":
                    functional_status = "met"
                    functional_evidence = ("Original pre-perturbation source checklist marked the feature "
                                           "path and every required behavior check met; no timing-only "
                                           "exclusion was present in that checklist.")
                else:
                    functional_status = "unknown"
                    functional_evidence = "Requires amended source judgment; original checklist mixed functional and timing premises."
                rows[f"{cohort}/{run_id}"] = {
                    "cohort": cohort, "run_id": run_id, "task_id": task["task_id"],
                    "source_path": original["source_path"],
                    "source_sha256": original["source_sha256"],
                    "original_oracle": run["oracle"],
                    "build": run["build"], "nominal": run["nominal"],
                    "functional": functional_status,
                    "functional_evidence": functional_evidence,
                    "timing_bound": timing_status,
                    "timing_evidence": timing_evidence,
                    "reviewer": "Codex retrospective split of frozen source; unblinded to early RTC outcomes",
                }
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    expected = source_rows()
    original_hashes = {cohort: sha256(ROOT / path) for cohort, (_, path) in COHORTS.items()}
    if args.init:
        if DECISIONS.exists():
            raise ValueError("Split-gate decision ledger already exists")
        ledger = {
            "schema_version": 1,
            "amendment_date": "2026-09-29",
            "retrospective_unblinded": True,
            "protocol_sha256": sha256(PROTOCOL),
            "original_oracle_review_sha256": original_hashes,
            "rq1_review_sha256": sha256(RQ1),
            "decisions": expected,
        }
        DECISIONS.write_text(json.dumps(ledger, sort_keys=True, indent=2) + "\n")
        print(f"Initialized {len(expected)} frozen-source split decisions; review exceptions before reporting")
        return
    ledger = json.loads(DECISIONS.read_text())
    if (ledger["protocol_sha256"] != sha256(PROTOCOL)
            or ledger["original_oracle_review_sha256"] != original_hashes
            or ledger["rq1_review_sha256"] != sha256(RQ1)):
        raise ValueError("A frozen source review or split-gate protocol changed")
    if set(ledger["decisions"]) != set(expected):
        raise ValueError("Split-gate source inventory changed")
    reports = {}
    for cohort in COHORTS:
        rows = []
        for key, row in sorted(ledger["decisions"].items()):
            if row["cohort"] != cohort:
                continue
            fresh = expected[key]
            for field in ("cohort", "run_id", "task_id", "source_path", "source_sha256",
                          "original_oracle", "build", "nominal"):
                if row[field] != fresh[field]:
                    raise ValueError(f"Frozen run evidence changed: {key}: {field}")
            if sha256(ROOT / row["source_path"]) != row["source_sha256"]:
                raise ValueError(f"Frozen source changed: {key}")
            if row["functional"] not in FUNCTIONAL or row["timing_bound"] not in TIMING:
                raise ValueError(f"Invalid split judgment: {key}")
            if not row["functional_evidence"].strip() or not row["timing_evidence"].strip() or not row["reviewer"].strip():
                raise ValueError(f"Missing split evidence: {key}")
            if cohort == "luna_primary" and row["timing_bound"] != fresh["timing_bound"]:
                raise ValueError(f"RQ1 timing mapping changed: {key}")
            rows.append(row)
        amended = [r for r in rows if r["build"] == "pass" and r["nominal"] == "pass"
                   and r["functional"] == "met"]
        original = [r for r in rows if r["build"] == "pass" and r["nominal"] == "pass"
                    and r["original_oracle"] == "adequate"]
        reports[cohort] = {
            "planned": len(rows),
            "build": dict(Counter(r["build"] for r in rows)),
            "nominal": dict(Counter(r["nominal"] for r in rows)),
            "original_oracle": dict(Counter(r["original_oracle"] for r in rows)),
            "functional": dict(Counter(r["functional"] for r in rows)),
            "timing_bound": dict(Counter(r["timing_bound"] for r in rows)),
            "original_strict_eligible": len(original),
            "amended_functional_eligible": len(amended),
            "original_strict_eligible_ids": [r["run_id"] for r in original],
            "amended_functional_eligible_ids": [r["run_id"] for r in amended],
            "timing_among_amended_eligible": dict(Counter(r["timing_bound"] for r in amended)),
        }
    output = {
        "protocol_sha256": ledger["protocol_sha256"],
        "decision_ledger_sha256": sha256(DECISIONS),
        "retrospective_unblinded": True,
        "cohorts": reports,
        "sol_feasibility_pilot_excluded": True,
    }
    (ROOT / "results/phase2_split_gate_summary.json").write_text(
        json.dumps(output, sort_keys=True, indent=2) + "\n")
    for cohort, row in reports.items():
        print(f"{cohort}: original={row['original_strict_eligible']}/{row['planned']}, "
              f"amended={row['amended_functional_eligible']}/{row['planned']}, "
              f"timing among amended={row['timing_among_amended_eligible']}")


if __name__ == "__main__":
    main()
