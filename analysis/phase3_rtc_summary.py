#!/usr/bin/env python3
"""Audit Phase 3 RTC raw runs and summarize conditional flip rates."""

import hashlib
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "subjects/phase3_rtc/plan.json"
RESULTS = ROOT / "results/phase3_rtc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson(successes: int, trials: int) -> tuple[float, float] | None:
    if trials == 0:
        return None
    z = 1.959963984540054
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    radius = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return (max(0, centre - radius), min(1, centre + radius))


def main() -> None:
    plan = json.loads(PLAN.read_text())
    split_path = ROOT / "analysis/phase2_split_gate_decisions.json"
    split = json.loads(split_path.read_text())["decisions"]
    plan_hash = sha256(PLAN)
    if sha256(ROOT / plan["protocol"]) != plan["protocol_sha256"]:
        raise ValueError("Registered protocol changed")
    records = {}
    canonical_platform = None
    for path in (RESULTS / "records").glob("*.json"):
        row = json.loads(path.read_text())
        ident, condition, index = row["version_id"], row["condition"], row["index"]
        expected_name = (f"{ident}-{condition}-{index:03d}.json"
                         if condition in ("nominal", "seeded") else f"{ident}-{condition}.json")
        if path.name != expected_name or row["run_id"] != path.stem:
            raise ValueError(f"Record naming mismatch: {path}")
        if row["plan_sha256"] != plan_hash or row["zephyr_commit"] != plan["zephyr_commit"]:
            raise ValueError(f"Plan or commit mismatch: {path}")
        if ident not in plan["versions"]:
            raise ValueError(f"Unregistered version: {ident}")
        version = plan["versions"][ident]
        for key in ("source", "elf"):
            if (row[key + "_path"] != version[key]
                    or row[key + "_sha256"] != version[key + "_sha256"]
                    or sha256(ROOT / version[key]) != version[key + "_sha256"]):
                raise ValueError(f"Frozen {key} mismatch: {path}")
        if row["renode_version"] != plan["renode_version"]:
            raise ValueError(f"Renode version mismatch: {path}")
        for key in ("cpu_performance_mips", "systick_frequency_hz", "quantum_ns",
                    "step_ns", "max_virtual_sec"):
            if row[key] != plan[key]:
                raise ValueError(f"Frozen simulator setting changed: {path}: {key}")
        expected_hz = (32000 if condition == "nominal" else
                       plan["seeded_frequencies_hz"][index] if condition == "seeded" else
                       plan["endpoints_hz"][condition])
        if row["lsi_frequency_hz"] != expected_hz:
            raise ValueError(f"Frequency mismatch: {path}")
        platform_text = (ROOT / row["platform_path"]).read_text()
        lsi_setting = f"wakeupTimerFrequency: {expected_hz}"
        if platform_text.count(lsi_setting) != 1 or platform_text.count("systickFrequency: 16000000") != 1:
            raise ValueError(f"Platform frequency setting mismatch: {path}")
        canonical = platform_text.replace(lsi_setting, "wakeupTimerFrequency: <LSI>")
        if canonical_platform is None:
            canonical_platform = canonical
        elif canonical != canonical_platform:
            raise ValueError(f"Platform changed beyond the registered RTC input: {path}")
        for artifact in ("platform", "uart", "monitor", "trace"):
            if row[artifact + "_sha256"] is not None and sha256(ROOT / row[artifact + "_path"]) != row[artifact + "_sha256"]:
                raise ValueError(f"{artifact} hash mismatch: {path}")
        trace = json.loads((ROOT / row["trace_path"]).read_text())
        if trace["outcome"] != row["outcome"] or trace["cases"] != row["cases"]:
            raise ValueError(f"Trace verdict mismatch: {path}")
        if row["outcome"] in ("pass", "fail") and not any(
                c["case"] == version["case"] and c["status"] == row["outcome"]
                for c in row["cases"]):
            raise ValueError(f"Selected case verdict missing: {path}")
        key = (ident, condition, index)
        if key in records:
            raise ValueError(f"Duplicate raw run: {key}")
        records[key] = row

    versions = {}
    for ident, version in plan["versions"].items():
        nominal = [records.get((ident, "nominal", i)) for i in range(plan["nominal_repeats"])]
        seeded = [records.get((ident, "seeded", i)) for i in range(plan["seed_count"])]
        nominal_status = dict(Counter(x["outcome"] if x else "missing" for x in nominal))
        seed_status = dict(Counter(x["outcome"] if x else "missing" for x in seeded))
        eligible = all(x is not None and x["outcome"] == "pass" for x in nominal)
        evaluable = seed_status.get("pass", 0) + seed_status.get("fail", 0)
        failures = seed_status.get("fail", 0)
        split_row = (split["luna_primary/rtc_alarm_callback-r04"] if ident == "luna_primary_r04"
                     else split["rtc_bound_supplement/rtc_alarm_callback-r05"]
                     if ident == "rtc_bound_r05" else None)
        old_gate = (bool(split_row and split_row["original_oracle"] == "adequate")
                    if split_row else None)
        amended_gate = (bool(split_row and split_row["functional"] == "met")
                        if split_row else None)
        versions[ident] = {
            "cohort": version["cohort"],
            "phase2_oracle_adequate": version["phase2_oracle_adequate"],
            "original_strict_gate": old_gate,
            "amended_functional_gate": amended_gate,
            "timing_bound_status": split_row["timing_bound"] if split_row else None,
            "nominal_repeats": nominal_status,
            "nominal_5_of_5": eligible,
            "seeded_statuses": seed_status,
            "registered_seed_count": plan["seed_count"],
            "distinct_seeded_frequencies": len(set(plan["seeded_frequencies_hz"])),
            "evaluable": evaluable,
            "pass_to_fail": failures if eligible else None,
            "original_strict_gate_flips": failures if eligible and old_gate else None,
            "amended_functional_gate_flips": failures if eligible and amended_gate else None,
            "flip_rate": failures / evaluable if eligible and evaluable else None,
            "wilson_95": wilson(failures, evaluable) if eligible else None,
            "endpoints": {end: records[(ident, end, 0)]["outcome"]
                          if (ident, end, 0) in records else "missing"
                          for end in ("min", "max")},
        }
    pairwise = {}
    for left, right in (("upstream", "luna_primary_r04"),
                        ("upstream", "rtc_bound_r05"),
                        ("luna_primary_r04", "rtc_bound_r05")):
        paired = [i for i in range(plan["seed_count"])
                  if (left, "seeded", i) in records and (right, "seeded", i) in records
                  and records[(left, "seeded", i)]["outcome"] in ("pass", "fail")
                  and records[(right, "seeded", i)]["outcome"] in ("pass", "fail")]
        pairwise[f"{left}__{right}"] = {
            "evaluable_paired_seeds": len(paired),
            "both_pass": sum(records[(left, "seeded", i)]["outcome"] == "pass" and
                             records[(right, "seeded", i)]["outcome"] == "pass" for i in paired),
            "both_fail": sum(records[(left, "seeded", i)]["outcome"] == "fail" and
                             records[(right, "seeded", i)]["outcome"] == "fail" for i in paired),
            "left_only_fail": sum(records[(left, "seeded", i)]["outcome"] == "fail" and
                                  records[(right, "seeded", i)]["outcome"] == "pass" for i in paired),
            "right_only_fail": sum(records[(left, "seeded", i)]["outcome"] == "pass" and
                                   records[(right, "seeded", i)]["outcome"] == "fail" for i in paired),
        }
    summary = {"plan_sha256": plan_hash, "split_gate_decisions_sha256": sha256(split_path),
               "split_gate_is_retrospective_unblinded": True,
               "raw_record_count": len(records),
               "versions": versions, "pairwise": pairwise,
               "scope_note": "Selected RTC case. Original strict gate excludes both agent suites; amended functional gate includes the primary Luna r04 and separate context-supplement r05. Amended reanalysis is retrospective/unblinded; no robustness-success or model-improvement claim."}
    (RESULTS / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    paired_path = RESULTS / "paired_schedules.csv"
    with paired_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["seed", "lsi_frequency_hz", "upstream", "luna_primary_r04", "rtc_bound_r05"])
        for i, hz in enumerate(plan["seeded_frequencies_hz"]):
            writer.writerow([i, hz] + [records[(ident, "seeded", i)]["outcome"]
                                      if (ident, "seeded", i) in records else "missing"
                                      for ident in ("upstream", "luna_primary_r04", "rtc_bound_r05")])
    print(f"audited {len(records)} raw runs; seeded completions: " +
          ", ".join(f"{ident}={sum(x is not None for x in [records.get((ident, 'seeded', i)) for i in range(100)])}/100"
                    for ident in plan["versions"]))


if __name__ == "__main__":
    main()
