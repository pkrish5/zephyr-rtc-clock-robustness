#!/usr/bin/env python3
"""Validate raw RTC-LSI records and summarize the selected upstream callback case."""

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase1_lsi_alarm"
DECISIONS = ROOT / "analysis" / "phase1_lsi_rtc_classification_decisions.json"
LABELS = ("brittle test assumption", "genuine firmware race/bug",
          "simulator/peripheral-model artifact", "unknown")
MIN_HZ, NOMINAL_HZ, MAX_HZ = 17_000, 32_000, 47_000
SEEDS = range(30)


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


def validate_run(run: dict, build: dict):
    if (run["elf_sha256"] != build["elf_sha256"]
            or run["test_source_sha256"] != build["test_source_sha256"]
            or run["config_sha256"] != build["config_sha256"]
            or run["variant"] != "callback"
            or run["lsi_frequency_bound_hz"] != [MIN_HZ, MAX_HZ]
            or run["cpu_performance_mips"] != 16
            or run["systick_frequency_hz"] != 16_000_000
            or run["quantum_ns"] != 1000
            or run["step_ns"] != 500_000_000
            or run["max_virtual_sec"] != 60):
        raise ValueError(f"Frozen inputs or timing limits changed: {run['run_id']}")
    if sha256(ROOT / run["renode_platform_path"]) != run["renode_platform_sha256"]:
        raise ValueError(f"Platform changed: {run['run_id']}")
    if sha256(ROOT / run["trace_path"]) != run["trace_sha256"]:
        raise ValueError(f"Trace changed: {run['run_id']}")
    if run["uart_sha256"] is not None and sha256(ROOT / run["uart_path"]) != run["uart_sha256"]:
        raise ValueError(f"UART changed: {run['run_id']}")
    if not (ROOT / run["monitor_path"]).exists():
        raise ValueError(f"Monitor log missing: {run['run_id']}")
    trace = json.loads((ROOT / run["trace_path"]).read_text())
    if (trace["run_id"] != run["run_id"] or trace["outcome"] != run["outcome"]
            or trace["lsi_frequency_hz"] != run["lsi_frequency_hz"]):
        raise ValueError(f"Trace/record mismatch: {run['run_id']}")
    expected = (NOMINAL_HZ if run["condition"] == "nominal" else
                MIN_HZ if run["condition"] == "min" else
                MAX_HZ if run["condition"] == "max" else
                random.Random(run["seed"]).randint(MIN_HZ, MAX_HZ))
    if run["lsi_frequency_hz"] != expected:
        raise ValueError(f"Seed/frequency mismatch: {run['run_id']}")
    return trace


def main():
    build = json.loads((RESULTS / "build.json").read_text())
    runs = [json.loads(line) for line in (RESULTS / "runs.jsonl").read_text().splitlines()]
    if len({r["run_id"] for r in runs}) != len(runs):
        raise ValueError("Duplicate run IDs")
    if len({(r["condition"], r["seed"]) for r in runs}) != len(runs):
        raise ValueError("Duplicate condition/seed pairs")
    if len({r["renode_version"] for r in runs}) != 1:
        raise ValueError("Simulator version changed between runs")
    traces = {r["run_id"]: validate_run(r, build) for r in runs}
    by_key = {(r["condition"], r["seed"]): r for r in runs}
    nominal = by_key.get(("nominal", 0))
    if nominal is None:
        raise ValueError("Nominal run missing")
    eligible = nominal["outcome"] == "pass"
    decisions = json.loads(DECISIONS.read_text()) if DECISIONS.exists() else {}
    replays_path = RESULTS / "replays.jsonl"
    replays = {r["run_id"]: r for r in map(json.loads, replays_path.read_text().splitlines())} if replays_path.exists() else {}
    flips = []
    unknown_runs = []
    classifications = []
    statuses = {}
    for seed in SEEDS:
        run = by_key.get(("perturbed", seed))
        if run is None:
            unknown_runs.append({"seed": seed, "reason": "missing"})
            continue
        statuses[seed] = run["outcome"]
        if run["outcome"] == "fail" and eligible:
            flips.append(run["run_id"])
            decision = decisions.get(run["run_id"], {"label": "unknown", "reason": "Pending four-way triage"})
            if decision["label"] not in LABELS or not decision.get("reason"):
                raise ValueError(f"Invalid classification: {run['run_id']}")
            if decision["label"] != "unknown" and not replays.get(run["run_id"], {}).get("identical_trace_and_verdict"):
                raise ValueError(f"Non-unknown flip lacks an identical replay: {run['run_id']}")
            classifications.append({"run_id": run["run_id"], **decision,
                                    "replay_identical": replays.get(run["run_id"], {}).get("identical_trace_and_verdict")})
        elif run["outcome"] in ("timeout", "harness_error"):
            unknown_runs.append({"seed": seed, "run_id": run["run_id"], "reason": run["outcome"]})
        elif run["outcome"] not in ("pass", "fail"):
            raise ValueError(f"Unexpected outcome: {run['run_id']}")
    endpoint = {}
    for condition in ("min", "max"):
        run = by_key.get((condition, 0))
        if run:
            endpoint[condition] = {"run_id": run["run_id"], "outcome": run["outcome"],
                                   "frequency_hz": run["lsi_frequency_hz"],
                                   "replay_identical": replays.get(run["run_id"], {}).get("identical_trace_and_verdict")}
            if run["outcome"] == "fail" and eligible:
                decision = decisions.get(run["run_id"], {"label": "unknown", "reason": "Endpoint flip pending four-way triage"})
                if decision["label"] not in LABELS or not decision.get("reason"):
                    raise ValueError(f"Invalid endpoint classification: {run['run_id']}")
                if decision["label"] != "unknown" and not replays.get(run["run_id"], {}).get("identical_trace_and_verdict"):
                    raise ValueError(f"Non-unknown endpoint lacks an identical replay: {run['run_id']}")
                classifications.append({"run_id": run["run_id"], **decision,
                                        "replay_identical": replays.get(run["run_id"], {}).get("identical_trace_and_verdict")})
    classified_ids = {item["run_id"] for item in classifications}
    if set(decisions) - classified_ids:
        raise ValueError(f"Classification decisions for non-flips: {sorted(set(decisions) - classified_ids)}")
    known = sum(status in ("pass", "fail") for status in statuses.values())
    summary = {
        "protocol": "subjects/phase1_lsi_rtc/PROTOCOL.md",
        "subject": "upstream rtc_api.test_alarm_callback linked unchanged into a selected-case wrapper",
        "upstream_commit": build["upstream_commit"],
        "board": build["board"],
        "nominal_run_id": nominal["run_id"],
        "nominal_outcome": nominal["outcome"],
        "nominal_cases": traces[nominal["run_id"]]["cases"],
        "eligible": eligible,
        "planned_seeded_runs": len(SEEDS),
        "recorded_seeded_runs": len(statuses),
        "evaluable_seeded_runs": known,
        "seeded_flip_count": len(flips),
        "seeded_flip_rate_known_runs": len(flips) / known if known else None,
        "wilson_95_known_runs": wilson(len(flips), known),
        "unknown_or_missing_runs": unknown_runs,
        "flipped_run_ids": flips,
        "endpoints": endpoint,
        "classification_counts_seeded": {
            label: sum(c["label"] == label and c["run_id"] in flips for c in classifications)
            for label in LABELS},
        "classification_counts_endpoints": {
            label: sum(c["label"] == label and c["run_id"] not in flips for c in classifications)
            for label in LABELS},
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    (RESULTS / "classifications.json").write_text(json.dumps(classifications, sort_keys=True, indent=2) + "\n")
    print(f"eligible={eligible} recorded={len(statuses)}/30 evaluable={known} flips={len(flips)} unknown={len(unknown_runs)}")


if __name__ == "__main__":
    main()
