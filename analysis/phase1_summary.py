#!/usr/bin/env python3
"""Validate Phase 1 raw records and summarize the preregistered human baseline."""

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase1"
MANIFEST = json.loads((ROOT / "subjects" / "phase1_zephyr" / "candidates.json").read_text())
SEEDS = range(30)
LABELS = ("brittle test assumption", "genuine firmware race/bug",
          "simulator/peripheral-model artifact", "unknown")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(flips: int, count: int) -> list[float] | None:
    if not count:
        return None
    z = 1.959963984540054
    p = flips / count
    base = 1 + z * z / count
    center = (p + z * z / (2 * count)) / base
    spread = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / base
    return [max(0, center - spread), min(1, center + spread)]


def case_map(record: dict) -> dict[str, str]:
    path = ROOT / record["trace_path"]
    platform = ROOT / record["renode_platform_path"]
    if sha256(platform) != record["renode_platform_sha256"]:
        raise ValueError(f"Platform description changed: {record['run_id']}")
    if sha256(path) != record["trace_sha256"]:
        raise ValueError(f"Trace changed: {path}")
    if record["uart_sha256"] and sha256(ROOT / record["uart_path"]) != record["uart_sha256"]:
        raise ValueError(f"UART output changed: {record['run_id']}")
    trace = json.loads(path.read_text())
    if trace["run_id"] != record["run_id"] or trace["outcome"] != record["outcome"]:
        raise ValueError(f"Trace/record mismatch: {record['run_id']}")
    cases = {}
    for case in trace["cases"]:
        if case["case"] in cases:
            raise ValueError(f"Duplicate case: {record['run_id']} {case['case']}")
        cases[case["case"]] = case["status"]
    return cases


def main():
    runs_path = RESULTS / "runs.jsonl"
    builds_path = RESULTS / "builds.jsonl"
    runs = [json.loads(line) for line in runs_path.read_text().splitlines()]
    builds = {entry["subject_id"]: entry for entry in map(json.loads, builds_path.read_text().splitlines())}
    if len({run["run_id"] for run in runs}) != len(runs):
        raise ValueError("Duplicate raw run IDs")
    for run in runs:
        build = builds[run["subject_id"]]
        if (run["elf_sha256"] != build["elf_sha256"]
                or run["source_tree_sha256"] != build["source_tree_sha256"]
                or run["board_overlay_sha256"] != build["overlay_sha256"]):
            raise ValueError(f"Build/source hash mismatch: {run['run_id']}")
        case_map(run)
    by_key = {(run["subject_id"], run["condition"], run["seed"], run["cpu_performance_mips"]): run for run in runs}
    excluded = []
    subjects = {}
    classifications = []
    for candidate in MANIFEST["subjects"]:
        ident = candidate["id"]
        build = builds.get(ident)
        if not build or build["exit_code"] != 0:
            excluded.append({"subject_id": ident, "reason": "build failure"})
            continue
        nominal = by_key.get((ident, "nominal", 0, 16))
        if not nominal:
            excluded.append({"subject_id": ident, "reason": "nominal run missing"})
            continue
        if nominal["elf_sha256"] != build["elf_sha256"]:
            raise ValueError(f"Build hash mismatch: {ident}")
        nominal_cases = case_map(nominal)
        if nominal["outcome"] != "pass":
            excluded.append({"subject_id": ident, "reason": f"nominal {nominal['outcome']}",
                             "case_counts": nominal["case_counts"], "run_id": nominal["run_id"]})
            continue
        flips = []
        unknown_runs = []
        case_flips = Counter()
        case_unknown = Counter()
        frequencies = []
        for seed in SEEDS:
            run = by_key.get((ident, "perturbed", seed, 16))
            if run is None:
                unknown_runs.append({"seed": seed, "reason": "missing"})
                for case, status in nominal_cases.items():
                    if status == "pass":
                        case_unknown[case] += 1
                continue
            expected = random.Random(seed).randint(15_840_000, 16_160_000)
            if (run["frequency_hz"] != expected or run["elf_sha256"] != nominal["elf_sha256"]
                    or run["source_tree_sha256"] != nominal["source_tree_sha256"]
                    or run["renode_version"] != nominal["renode_version"]
                    or run["cpu_performance_mips"] != 16 or run["quantum_ns"] != 1000
                    or run["frequency_bound_hz"] != [15_840_000, 16_160_000]):
                raise ValueError(f"Frozen binary/source or schedule mismatch: {run['run_id']}")
            frequencies.append(run["frequency_hz"])
            cases = case_map(run)
            if run["outcome"] == "fail":
                flips.append(run["run_id"])
                classifications.append({"run_id": run["run_id"], "label": "unknown",
                                        "reason": "Pending written four-way triage and replay", "trace_path": run["trace_path"]})
            elif run["outcome"] in ("timeout", "harness_error"):
                unknown_runs.append({"seed": seed, "run_id": run["run_id"], "reason": run["outcome"]})
            elif run["outcome"] != "pass":
                raise ValueError(f"Unexpected outcome: {run['run_id']}")
            for case, status in nominal_cases.items():
                if status != "pass":
                    continue
                trial_status = cases.get(case)
                if trial_status == "fail":
                    case_flips[case] += 1
                elif trial_status != "pass":
                    case_unknown[case] += 1
        boundary = {}
        for condition in ("min", "max"):
            run = by_key.get((ident, condition, 0, 16))
            if run:
                expected = 15_840_000 if condition == "min" else 16_160_000
                if run["frequency_hz"] != expected or run["elf_sha256"] != nominal["elf_sha256"]:
                    raise ValueError(f"Invalid boundary schedule: {run['run_id']}")
                case_map(run)
                boundary[condition] = {"run_id": run["run_id"], "outcome": run["outcome"],
                                       "case_counts": run["case_counts"]}
                if run["outcome"] == "fail":
                    classifications.append({"run_id": run["run_id"], "label": "unknown",
                                            "reason": "Boundary-schedule flip pending written triage and replay",
                                            "trace_path": run["trace_path"]})
        completed = len(frequencies)
        known = completed - sum(item.get("reason") in ("timeout", "harness_error") for item in unknown_runs)
        subjects[ident] = {
            "upstream_path": candidate["path"],
            "interrupt_path": candidate["interrupt_path"],
            "nominal_run_id": nominal["run_id"],
            "nominal_case_counts": nominal["case_counts"],
            "planned_random_schedules": len(SEEDS),
            "recorded_random_schedules": completed,
            "frequency_hz_observed_range": [min(frequencies), max(frequencies)] if frequencies else None,
            "suite_flip_count": len(flips),
            "suite_flip_rate_of_planned": len(flips) / len(SEEDS),
            "wilson_95_known_runs": wilson(len(flips), known),
            "unknown_or_missing_runs": unknown_runs,
            "case_rates": {case: {"flips": case_flips[case],
                                  "unknown_or_missing": case_unknown[case],
                                  "wilson_95_known_runs": wilson(case_flips[case], len(SEEDS) - case_unknown[case])}
                           for case, status in nominal_cases.items() if status == "pass"},
            "flipped_run_ids": flips,
            "boundary_challenges": boundary,
        }
    summary = {
        "protocol": "subjects/phase1_zephyr/PROTOCOL.md",
        "upstream_commit": MANIFEST["zephyr_commit"],
        "board": MANIFEST["board"],
        "subjects": subjects,
        "excluded": excluded,
        "classification_counts": {label: sum(item["label"] == label for item in classifications) for label in LABELS},
        "pilot_note": "30 seeded schedules per nominally passing subject; one Zephyr repository and one board. Nominal 100-MIPS run excluded.",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    (RESULTS / "classifications.json").write_text(json.dumps(classifications, sort_keys=True, indent=2) + "\n")
    print(f"eligible={len(subjects)} excluded={len(excluded)} recorded_random={sum(x['recorded_random_schedules'] for x in subjects.values())} flips={sum(x['suite_flip_count'] for x in subjects.values())} unknown={sum(len(x['unknown_or_missing_runs']) for x in subjects.values())}")


if __name__ == "__main__":
    main()
