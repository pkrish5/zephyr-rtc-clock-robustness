#!/usr/bin/env python3
"""Audit a manual RQ1 source inventory against frozen primary candidates."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "results/phase2_luna/static_candidates.json"
DECISIONS = ROOT / "analysis/phase3_rq1_decisions.json"
OUTPUT = ROOT / "results/phase3_rq1_summary.json"
VALID = {"pending", "unjustified", "none_found", "unknown"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0, mid - radius), min(1, mid + radius)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    records = json.loads(CANDIDATES.read_text())["records"]
    expected = {}
    for record in records:
        ident = record.get("run_id", record.get("case"))
        if ident in expected:
            raise ValueError(f"Duplicate source unit: {ident}")
        if record["kind"] == "upstream":
            hashes = record["source_files_sha256"]
        else:
            source = ROOT / "generated/phase2_luna/suites" / record["task_id"] / ident.split("-")[-1] / "test.c"
            hashes = {str(source.relative_to(ROOT)): record["source_sha256"]}
        for path, digest in hashes.items():
            if sha256(ROOT / path) != digest:
                raise ValueError(f"Frozen source changed: {path}")
        expected[ident] = {"kind": record["kind"], "task_id": record["task_id"],
                           "source_files_sha256": hashes,
                           "status": "pending", "issues": [], "evidence": "", "reviewer": ""}
    if DECISIONS.exists():
        saved = json.loads(DECISIONS.read_text())
    else:
        if not args.init:
            raise ValueError("Run --init to create review inventory")
        saved = {"schema_version": 1, "rubric": "analysis/PHASE3_RQ1_CODING.md",
                 "rubric_sha256": sha256(ROOT / "analysis/PHASE3_RQ1_CODING.md"),
                 "source_candidate_sha256": sha256(CANDIDATES),
                 "reviewer_note": "One reviewer; paper claims require independent adjudication.",
                 "decisions": expected}
        DECISIONS.write_text(json.dumps(saved, sort_keys=True, indent=2) + "\n")
    if saved["rubric_sha256"] != sha256(ROOT / saved["rubric"]):
        raise ValueError("RQ1 rubric changed")
    if saved["source_candidate_sha256"] != sha256(CANDIDATES):
        raise ValueError("Static candidate input changed")
    if set(saved["decisions"]) != set(expected):
        raise ValueError("Source inventory changed")
    for ident, row in saved["decisions"].items():
        template = expected[ident]
        if any(row[key] != template[key] for key in ("kind", "task_id", "source_files_sha256")):
            raise ValueError(f"Source metadata changed: {ident}")
        if row["status"] not in VALID:
            raise ValueError(f"Invalid status: {ident}")
        if row["status"] != "pending" and (not row["evidence"].strip() or not row["reviewer"].strip()):
            raise ValueError(f"Missing review evidence: {ident}")
        if row["status"] == "unjustified" and not row["issues"]:
            raise ValueError(f"Missing issue for unjustified source: {ident}")
        for issue in row["issues"]:
            if issue["path"] not in row["source_files_sha256"]:
                raise ValueError(f"Issue points outside source: {ident}")
            if not isinstance(issue["line"], int) or issue["line"] < 1 or not issue["category"] or not issue["reason"]:
                raise ValueError(f"Malformed issue: {ident}")
    groups = {}
    for kind in ("agent", "upstream"):
        rows = [row for row in saved["decisions"].values() if row["kind"] == kind]
        counts = {status: sum(row["status"] == status for row in rows) for status in VALID}
        groups[kind] = {"registered_units": len(rows), "status_counts": counts,
                        "unjustified_fraction": counts["unjustified"] / len(rows),
                        "unjustified_wilson_95": wilson(counts["unjustified"], len(rows))}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"status": "exploratory_one_reviewer",
                                  "decisions_sha256": sha256(DECISIONS),
                                  "groups": groups}, sort_keys=True, indent=2) + "\n")
    print("RQ1: " + ", ".join(f"{kind}={group['status_counts']}"
                              for kind, group in groups.items()))


if __name__ == "__main__":
    main()
