#!/usr/bin/env python3
"""Audit selected RTC nominal screens and record explicit corpus decisions."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "counting": ("rtc_counting", "rtc_api.test_time_counting", 2),
    "alarm_pending": ("rtc_alarm_pending", "rtc_api.test_alarm", 1),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", choices=CONFIG)
    args = parser.parse_args()
    name, case, series = CONFIG[args.subject]
    results = ROOT / "results" / name
    build_path = results / "build.json"
    build = json.loads(build_path.read_text())
    if build["exit_code"] != 0 or sha(ROOT / build["elf_path"]) != build["elf_sha256"]:
        raise ValueError("Frozen selected-case build failed or changed")
    for path, digest in build["input_sha256"].items():
        if sha(ROOT / path) != digest:
            raise ValueError(f"Build input changed: {path}")
    all_records = []
    for path in sorted((results / "nominal_records").glob("*.json")):
        row = json.loads(path.read_text())
        if row["run_id"] != path.stem or row["case"] != case:
            raise ValueError(f"Run identity mismatch: {path}")
        if row["elf_sha256"] != build["elf_sha256"] or row["build_record_sha256"] != sha(build_path):
            raise ValueError(f"Frozen build mismatch: {path}")
        if row["lsi_frequency_hz"] != 32000 or row["cpu_performance_mips"] != 16 or row["systick_frequency_hz"] != 16000000 or row["quantum_ns"] != 1000:
            raise ValueError(f"Nominal settings changed: {path}")
        for artifact in ("platform", "uart", "monitor", "trace"):
            if row[artifact + "_sha256"] and sha(ROOT / row[artifact + "_path"]) != row[artifact + "_sha256"]:
                raise ValueError(f"Artifact changed: {path}: {artifact}")
        trace = json.loads((ROOT / row["trace_path"]).read_text())
        if trace["outcome"] != row["outcome"]:
            raise ValueError(f"Trace outcome changed: {path}")
        if row["outcome"] == "pass" and not any(c["case"] == case and c["status"] == "pass" for c in trace["cases"]):
            raise ValueError(f"Selected case pass missing: {path}")
        all_records.append(row)
    selected = [r for r in all_records if r.get("nominal_series", 1) == series]
    if len(selected) != 5 or sorted(r["run_id"] for r in selected) != sorted(
        f"{args.subject}-nominal-{'s2-' if series == 2 else ''}{i:03d}" for i in range(5)):
        raise ValueError("Five selected nominal screen records are required")
    eligible = all(r["outcome"] == "pass" for r in selected)
    decision = {
        "subject": args.subject, "case": case,
        "build_record_sha256": sha(build_path), "elf_sha256": build["elf_sha256"],
        "selected_nominal_series": series,
        "selected_run_ids": [r["run_id"] for r in selected],
        "selected_outcomes": dict(Counter(r["outcome"] for r in selected)),
        "all_nominal_attempt_outcomes": dict(Counter(r["outcome"] for r in all_records)),
        "initial_sandbox_harness_errors_retained": (args.subject == "counting" and
                                                    sum(r["outcome"] == "harness_error" and
                                                        r.get("nominal_series", 1) == 1
                                                        for r in all_records) == 5),
        "qualified_for_proposed_task_list": eligible,
        "scope": "Adjacent LSI-driven RTC behavior, not an ISR callback test",
    }
    output = results / "qualification.json"
    if output.exists() and json.loads(output.read_text()) != decision:
        raise ValueError("Prior qualification decision changed")
    if not output.exists():
        output.write_text(json.dumps(decision, sort_keys=True, indent=2) + "\n")
    print(f"{args.subject}: selected 5-run screen={decision['selected_outcomes']}, "
          f"qualified={eligible}; all attempts={decision['all_nominal_attempt_outcomes']}")


if __name__ == "__main__":
    main()
