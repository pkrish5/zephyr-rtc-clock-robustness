#!/usr/bin/env python3
"""Audit the exploratory nominal-clock RTC driver-delay pilot."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_latency_pilot"
OUT = ROOT / "analysis/rtc_latency_pilot"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    m = read(BASE / "manifest.json")
    smoke = read(BASE / "tick_smoke_audit.json")
    if not smoke["validated"] or smoke["manifest_sha256"] != sha(BASE / "manifest.json"):
        raise RuntimeError("One-tick mechanism smoke invalid")
    records = {}
    builds = {}
    for rid in m["suite_ids"]:
        for level in m["levels_us"]:
            build_path = BASE / "builds" / rid / str(level) / "build_record.json"
            if not build_path.exists():
                continue
            b = read(build_path)
            builds[(rid, level)] = b
            for rel, digest in b["inputs"].items():
                if sha(ROOT / rel) != digest:
                    raise RuntimeError(f"Build input changed: {rel}")
            if b["status"] != "pass":
                continue
            elf = ROOT / b["elf_path"]
            if sha(elf) != b["elf_sha256"]:
                raise RuntimeError(f"ELF changed: {rid} {level}")
            path = BASE / "records" / f"{rid}-{level}us.json"
            if not path.exists():
                continue
            r = read(path)
            if (r["manifest_sha256"] != sha(BASE / "manifest.json") or
                    r["elf_sha256"] != b["elf_sha256"] or
                    r["source_sha256"] != m["suite_versions"][rid]["source_sha256"] or
                    r["platform_sha256"] != m["platform_sha256"] or
                    r["renode_version"] != m["renode_version"] or
                    r["delay_us"] != level):
                raise RuntimeError(f"Record fields mismatch: {path}")
            for part in ("trace", "uart", "monitor"):
                if sha(ROOT / r[f"{part}_path"]) != r[f"{part}_sha256"]:
                    raise RuntimeError(f"Artifact changed: {path} {part}")
            records[(rid, level)] = r
    rows = []
    for rid in m["suite_ids"]:
        v = m["suite_versions"][rid]
        group = ("human_control" if v["kind"] == "human" else
                 "definite" if rid in m["definite_ids"] else "sampled_unknown")
        control = records.get((rid, 0))
        for level in m["levels_us"]:
            r = records.get((rid, level))
            b = builds.get((rid, level))
            measurements = [] if r is None else r["delay_measurements"]
            achieved = [d["achieved_us"] for d in measurements
                        if d["requested_us"] == level]
            valid_exposure = (level == 0 or bool(achieved) and
                              all(0.9 * level <= x <= 1.1 * level + 50
                                  for x in achieved))
            flip = bool(level > 0 and control is not None and
                        control["outcome"] == "pass" and r is not None and
                        r["outcome"] == "fail" and valid_exposure)
            rows.append({"suite_id": rid, "family": v["family"],
                         "kind": v["kind"], "model": v["model"],
                         "prompt_condition": v["prompt_condition"],
                         "group": group, "delay_us": level,
                         "build_status": None if b is None else b["status"],
                         "outcome": None if r is None else r["outcome"],
                         "control_outcome": None if control is None else control["outcome"],
                         "achieved_min_us": min(achieved) if achieved else None,
                         "achieved_max_us": max(achieved) if achieved else None,
                         "delay_measurement_count": len(achieved),
                         "valid_exposure": valid_exposure,
                         "induced_fail": flip,
                         "record_path": None if r is None else r["run_id"]})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "rows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary = {"registered_suites": len(m["suite_ids"]),
               "registered_runs": len(m["suite_ids"]) * len(m["levels_us"]),
               "build_records": len(builds), "simulator_records": len(records),
               "smoke_validated": True,
               "outcome_counts": dict(Counter(str(r["outcome"]) for r in records.values())),
               "control_outcome_counts": dict(Counter(str(records[(rid, 0)]["outcome"])
                                                      for rid in m["suite_ids"]
                                                      if (rid, 0) in records)),
               "induced_failures": [r for r in rows if r["induced_fail"]],
               "injection_missing_or_out_of_tolerance": [r for r in rows
                   if r["delay_us"] > 0 and r["outcome"] is not None and
                   not r["valid_exposure"]],
               "group_counts": dict(Counter(r["group"] for r in rows if r["delay_us"] == 0))}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("records", len(records), "/", summary["registered_runs"],
          "induced failures", len(summary["induced_failures"]))


if __name__ == "__main__":
    main()
