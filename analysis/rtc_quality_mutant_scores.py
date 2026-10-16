#!/usr/bin/env python3
"""Audit immutable RTC quality-mutant records and report suite/cell scores."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TWO = ROOT / "results/rtc_timing_mutants_two_faults"
THIRD = ROOT / "results/rtc_nonarrival_driver_v3"
RESUME = ROOT / "results/rtc_nonarrival_driver_v3_resume"
OUT = ROOT / "analysis/rtc_quality_mutant_scores"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_record(path, expected_manifest):
    r = read(path)
    if r["manifest_sha256"] != sha(expected_manifest):
        raise RuntimeError(f"Manifest mismatch: {path}")
    for name in ("trace", "uart", "monitor"):
        artifact = ROOT / r[f"{name}_path"]
        digest = r[f"{name}_sha256"]
        if digest is None and r["outcome"] == "harness_error" and not artifact.exists():
            continue
        if not artifact.exists() or sha(artifact) != digest:
            raise RuntimeError(f"Saved artifact mismatch: {path} {name}")
    if sha(ROOT / r["platform_path"]) != r["platform_sha256"]:
        raise RuntimeError(f"Platform mismatch: {path}")
    if r["renode_version"] != read(expected_manifest)["renode_version"]:
        raise RuntimeError(f"Simulator version mismatch: {path}")
    return r


def main():
    two_manifest, third_manifest = read(TWO / "manifest.json"), read(THIRD / "manifest.json")
    activation = read(ROOT / "results/rtc_timing_mutants/activation_audit.json")
    valid = {(x["family"], x["operator"]) for x in activation["rows"]
             if x.get("activated") is True}
    if len(valid) != 6:
        raise RuntimeError("Early/late reference activation incomplete")
    third_activation = THIRD / "activation_audit.json"
    use_third = third_activation.exists() and read(third_activation)["status"] == "validated"
    if use_third and sha(THIRD / "manifest.json") != read(third_activation)["manifest_sha256"]:
        raise RuntimeError("Third-fault activation manifest mismatch")
    resume_manifest = RESUME / "manifest.json"
    resumed = read(resume_manifest) if resume_manifest.exists() else None
    if resumed and resumed["original_manifest_sha256"] != sha(THIRD / "manifest.json"):
        raise RuntimeError("Recovery registration references another original manifest")
    rows = []
    for suite_id, version in sorted(two_manifest["versions"].items()):
        for operator in ("late", "early") + (("nonarrival",) if use_third else ()):
            base = THIRD if operator == "nonarrival" else TWO
            path = base / "records" / f"{suite_id}{'' if operator == 'nonarrival' else '-' + operator}.json"
            if operator == "nonarrival" and not path.exists() and resumed:
                if suite_id not in resumed["suites"]:
                    raise RuntimeError(f"Unregistered recovery suite: {suite_id}")
                base = RESUME
                path = base / "records" / f"{suite_id}.json"
            if not path.exists():
                continue
            r = audit_record(path, base / "manifest.json")
            if r["suite_id"] != suite_id or r["family"] != version["family"]:
                raise RuntimeError(f"Suite mismatch: {path}")
            if r["source_sha256"] != version["source_sha256"]:
                raise RuntimeError(f"Source mismatch: {path}")
            if operator == "nonarrival":
                build_record = THIRD / "builds" / suite_id / "build_record.json"
                if not build_record.exists() or read(build_record)["status"] != "pass":
                    raise RuntimeError(f"Nonarrival build missing: {suite_id}")
                expected_elf_sha = read(build_record)["elf_sha256"]
                elf_path = ROOT / read(build_record)["elf_path"]
            else:
                expected_elf_sha = version["elf_sha256"]
                elf_path = ROOT / version["elf_path"]
            if r["elf_sha256"] != expected_elf_sha or sha(elf_path) != expected_elf_sha:
                raise RuntimeError(f"ELF mismatch: {path}")
            if r["outcome"] not in ("pass", "fail", "timeout", "unknown", "harness_error"):
                raise RuntimeError(f"Unknown verdict: {path}")
            rows.append({"suite_id": suite_id, "family": version["family"],
                         "kind": version["kind"], "model": version["model"],
                         "prompt_condition": version["prompt_condition"],
                         "operator": operator, "outcome": r["outcome"],
                         "kill": "yes" if r["outcome"] == "fail" else
                                 "no" if r["outcome"] == "pass" else "missing",
                         "record_path": str(path.relative_to(ROOT)),
                         "record_sha256": sha(path)})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "rows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    totals = Counter((r["model"], r["prompt_condition"], r["operator"], r["kill"])
                     for r in rows)
    summary = {
        "status": ("three_faults_complete" if use_third and
                   sum(r["operator"] == "nonarrival" for r in rows) == 69 else
                   "third_fault_in_progress" if use_third else "interim_two_faults"),
        "expected_two_fault_records": 138,
        "observed_two_fault_records": sum(r["operator"] != "nonarrival" for r in rows),
        "expected_third_fault_records": 69 if use_third else 0,
        "observed_third_fault_records": sum(r["operator"] == "nonarrival" for r in rows),
        "original_third_fault_records": sum(r["operator"] == "nonarrival" and
                                            r["record_path"].startswith(str(THIRD.relative_to(ROOT)) + "/")
                                            for r in rows),
        "recovery_third_fault_records": sum(r["operator"] == "nonarrival" and
                                            r["record_path"].startswith(str(RESUME.relative_to(ROOT)) + "/")
                                            for r in rows),
        "cells": [{"model": model, "prompt_condition": prompt, "operator": operator,
                   "kill": kill, "count": n}
                  for (model, prompt, operator, kill), n in sorted(
                      totals.items(), key=lambda item: tuple(str(v) for v in item[0]))],
        "suite_scores": []}
    by_suite = defaultdict(list)
    for r in rows:
        by_suite[r["suite_id"]].append(r)
    for suite_id, suite_rows in sorted(by_suite.items()):
        known = sum(r["kill"] in ("yes", "no") for r in suite_rows)
        killed = sum(r["kill"] == "yes" for r in suite_rows)
        summary["suite_scores"].append({"suite_id": suite_id,
                                        "family": suite_rows[0]["family"],
                                        "model": suite_rows[0]["model"],
                                        "prompt_condition": suite_rows[0]["prompt_condition"],
                                        "killed": killed, "known": known,
                                        "planned": 3 if use_third else 2})
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(summary["status"], "two", summary["observed_two_fault_records"],
          "third", summary["observed_third_fault_records"])


if __name__ == "__main__":
    main()
