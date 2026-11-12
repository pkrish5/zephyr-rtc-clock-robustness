#!/usr/bin/env python3
"""Derive the separate full-application counter table from verified records."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ORIGINAL = ROOT / "artifacts/s2_production_20261026_v1/returned_20261027_v1/bundle/results/s2_production_20261026_v1/records"
RECOVERY = ROOT / "notes/counter_repair_execution_2026-11-05_v1"
DIAGNOSTIC = ROOT / "notes/counter_verification_2026-11-11_v1/report-3575326-v1/summary.json"
REPEAT = ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/combined_report_v1/summary.json"
CASES = [
    "counter_basic.test_all_channels",
    "counter_basic.test_short_relative_alarm",
    "counter_basic.test_single_shot_alarm_notop",
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def key(record):
    return record["condition"], record.get("seed"), record["frequency_hz"]

def load_records(paths):
    records = {}
    hashes = {}
    for path in paths:
        record = json.loads(path.read_text())
        assert record["application_completed"] and not record["error"]
        assert not record["missing_cases"] and not record["duplicate_cases"]
        status = {c["case"]: c["status"] for c in record["cases"]}
        assert all(name in status for name in CASES)
        assert key(record) not in records
        records[key(record)] = status
        hashes[str(path.relative_to(ROOT))] = sha(path)
    assert len(records) == 102
    assert Counter(k[0] for k in records) == {"seeded": 100, "min": 1, "max": 1}
    return records, hashes

original, original_hashes = load_records(sorted(ORIGINAL.glob("f4-counter-*.json")))
all_records = {"V0": original}
all_hashes = dict(original_hashes)
for variant in ["V1", "V1b", "V2"]:
    paths = []
    for job in ["3570473", "3570474"]:
        directory = RECOVERY / f"verified-{job}-v1/output/records"
        paths.extend(p for p in directory.glob(f"f4-counter-{variant}-*.json")
                     if p.name.split("-")[2] == variant)
    records, hashes = load_records(sorted(paths))
    assert set(records) == set(original), variant
    all_records[variant] = records
    all_hashes.update(hashes)

counts = {}
for variant, records in all_records.items():
    counts[variant] = {}
    for name in CASES:
        c = Counter(row[name] for row in records.values())
        counts[variant][name] = {status: c[status] for status in ["pass", "fail", "skip"]}
        assert sum(c.values()) == 102

assert counts["V0"][CASES[0]] == {"pass": 58, "fail": 44, "skip": 0}
assert counts["V0"][CASES[1]] == {"pass": 58, "fail": 0, "skip": 44}
assert counts["V0"][CASES[2]] == {"pass": 58, "fail": 44, "skip": 0}
paired = {}
for variant in ["V1", "V1b", "V2"]:
    assert counts[variant][CASES[0]] == {"pass": 102, "fail": 0, "skip": 0}
    assert counts[variant][CASES[1]] == {"pass": 88, "fail": 14, "skip": 0}
    assert counts[variant][CASES[2]] == {"pass": 87, "fail": 15, "skip": 0}
    pairs = {name: Counter((original[k][name], all_records[variant][k][name])
                           for k in original) for name in CASES}
    assert pairs[CASES[0]][("fail", "pass")] == 44
    assert pairs[CASES[1]][("skip", "fail")] == 14
    assert pairs[CASES[2]][("fail", "pass")] == 29
    assert pairs[CASES[2]][("fail", "fail")] == 15
    paired[variant] = {name: {"/".join(k): n for k, n in pairs[name].items()}
                       for name in CASES}

fault_records = {}
fault_hashes = {}
fault_dir = RECOVERY / "verified-3570475-v1/output/records"
for path in sorted(fault_dir.glob("f4-counter-*.json")):
    r = json.loads(path.read_text())
    assert r["condition"] in ["slow_fault", "fast_fault"]
    variant = r["unit_id"].rsplit("-", 1)[-1]
    assert variant in all_records
    assert r["application_completed"] and not r["error"]
    selected = [c["status"] for c in r["cases"] if c["case"] == CASES[0]]
    assert len(selected) == 1
    fault_records.setdefault(variant, {})[r["condition"]] = selected[0]
    fault_hashes[str(path.relative_to(ROOT))] = sha(path)
assert len(fault_hashes) == 8
assert {v: fault_records[v]["slow_fault"] for v in all_records} == {
    "V0": "fail", "V1": "pass", "V1b": "fail", "V2": "fail"
}
assert all(fault_records[v]["fast_fault"] == "pass" for v in all_records)

diagnostic = json.loads(DIAGNOSTIC.read_text())
assert diagnostic["replay_launches_matched"] == 17
assert diagnostic["covered_primary_failure_slots"] == 87
assert diagnostic["functional_legal_case_counts"] == {
    "fail": 0, "missing": 0, "pass": 51, "skip": 0
}
assert diagnostic["activation_qualified"] is False
assert next(c for c in diagnostic["activation_controls"] if c["frequency_hz"] == 10000)["over_upper_ms"] == 18
repeat = json.loads(REPEAT.read_text())
assert repeat["planned_launches"] == 180 and repeat["all_30_agree_in_every_cell"]
assert not repeat["observed_mixed_pass_fail_cells"]

header = [
    r"\begin{tabular}{@{}lccc@{}}\toprule",
    r"Variant & All channels & Short relative & Single shot\\",
    r"\midrule",
]
for variant in ["V0", "V1", "V1b", "V2"]:
    values = []
    for name in CASES:
        c = counts[variant][name]
        values.append(f'{c["pass"]}/{c["fail"]}/{c["skip"]}')
    header.append(f'{variant} & ' + " & ".join(values) + r"\\")
header += [r"\bottomrule\end{tabular}", ""]
table = ROOT / "paper/draft/tables/counter_course_v3.tex"
table.write_text("\n".join(header))
audit = {
    "status": "PASS",
    "subject": "one upstream counter all-channels case in full F4 application",
    "settings_per_variant": 102,
    "counts": counts,
    "paired_transitions": paired,
    "raw_fault_selected_verdicts": fault_records,
    "slow_fault_activation_qualified": False,
    "diagnostic_replays_matched": 17,
    "functional_reference_failures_covered": 87,
    "functional_reference_case_passes": 51,
    "repeatability_launches": 180,
    "repeatability_mixed_cells": 0,
    "source_record_sha256": all_hashes | fault_hashes,
    "diagnostic_summary_sha256": sha(DIAGNOSTIC),
    "repeatability_summary_sha256": sha(REPEAT),
    "table_sha256": sha(table),
}
HERE.mkdir(exist_ok=True)
(HERE / "counter_table_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in audit.items()
                  if k not in ["source_record_sha256", "paired_transitions"]}, indent=2))
