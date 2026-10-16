#!/usr/bin/env python3
"""Audit completed RTC v2 originals, replays, forecasts, and rate bounds.

This reads locked inputs and raw results. It writes only a derived JSON summary.
"""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_factorial_v2"
OUT = ROOT / "analysis/rtc_factorial_v2_final_summary.json"
MANIFEST = json.loads((BASE / "manifest.json").read_text())
PLAN = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())
FORECAST = json.loads((ROOT / "analysis/rtc_threshold_sample_v1/forecast.json").read_text())
SAMPLE = json.loads((ROOT / "analysis/rtc_threshold_sample_v2/sample.json").read_text())
CLASSIFICATION = json.loads((ROOT / "analysis/rtc_factorial_v2_classification.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


require(not (BASE / "STOP_PREDICTION_MISMATCH.json").exists(), "prediction mismatch marker exists")
for worker in range(3):
    require((BASE / f"worker{worker}.log").read_text().strip().endswith("complete"),
            f"worker {worker} did not finish")

versions = MANIFEST["versions"]
forecast = {p["run_id"]: p for p in FORECAST["predictions"]}
sampled = set(SAMPLE["sampled_predictable_run_ids"])
require(len(versions) == 53 and len(forecast) == 66 and len(sampled) == 14, "cohort size changed")
require(len(set(versions) & set(forecast)) == 50, "measured AI set changed")
require(sampled <= set(versions), "sampled suite missing")
require(sum(p["prediction_status"] == "not_predictable" for p in forecast.values()) == 36,
        "not-predictable cohort changed")

records = {}
for path in (BASE / "records").glob("*.json"):
    row = json.loads(path.read_text())
    rid = row["suite_id"]
    key = (rid, row["condition"], row["seed"])
    require(key not in records, f"duplicate original {key}")
    require(rid in versions, f"unregistered suite {rid}")
    v = versions[rid]
    require(row["source_sha256"] == v["source_sha256"] and
            row["elf_sha256"] == v["elf_sha256"], f"frozen hash mismatch {key}")
    require(row["schedule_sha256"] == MANIFEST["schedule_sha256"] and
            row["renode_version"] == MANIFEST["renode_version"] and
            row["cpu_performance_mips"] == PLAN["cpu_performance_mips"] and
            row["systick_frequency_hz"] == PLAN["systick_frequency_hz"] and
            row["quantum_ns"] == PLAN["quantum_ns"], f"platform mismatch {key}")
    expected_hz = (PLAN["seeded_frequencies_hz"][row["seed"]] if row["condition"] == "seeded"
                   else PLAN["endpoints_hz"][row["condition"]])
    require(row["lsi_frequency_hz"] == expected_hz, f"frequency mismatch {key}")
    require(row["outcome"] in ("pass", "fail", "harness_error"), f"unrecognized verdict {key}")
    require(digest(ROOT / row["trace_path"]) == row["trace_sha256"], f"trace hash mismatch {key}")
    records[key] = row
require(len(records) == len(versions) * 102 == 5406, "original record count incomplete")
for rid in versions:
    for seed in range(100):
        require((rid, "seeded", seed) in records, f"missing seed {rid} {seed}")
    for endpoint in ("min", "max"):
        require((rid, endpoint, None) in records, f"missing endpoint {rid} {endpoint}")

for rid in sampled:
    expected = set(versions[rid]["predicted_failure_seeds"])
    for seed in range(100):
        outcome = records[(rid, "seeded", seed)]["outcome"]
        require(outcome in ("pass", "fail") and (outcome == "fail") == (seed in expected),
                f"sample mismatch or missing {rid} seed {seed}")

replays = {}
for path in (BASE / "replay_records").glob("*.json"):
    replay = json.loads(path.read_text())
    key = (replay["suite_id"], replay["condition"], replay["seed"])
    require(key not in replays and key in records, f"extra/duplicate replay {key}")
    original = records[key]
    require(original["outcome"] == replay["outcome"] == "fail", f"replay verdict differs {key}")
    require(digest(ROOT / replay["trace_path"]) == replay["trace_sha256"],
            f"replay trace hash mismatch {key}")
    a = json.loads((ROOT / original["trace_path"]).read_text())
    b = json.loads((ROOT / replay["trace_path"]).read_text())
    require(all(a[k] == b[k] for k in
                ("lsi_frequency_hz", "observations", "cases", "outcome", "error")),
            f"persisted replay differs {key}")
    replays[key] = replay
failed = {key for key, row in records.items() if row["outcome"] == "fail"}
require(set(replays) == failed, "not every original failure replayed exactly once")
classified = {x["run_id"]: x for x in CLASSIFICATION["rows"]}
require(len(classified) == len(failed) and set(classified) == {records[k]["run_id"] for k in failed},
        "classification ledger incomplete")
require(all(x["persisted_replay_identical"] for x in classified.values()),
        "classification replay field differs")

cells = defaultdict(lambda: dict(suites=0, measured_suites=0, predicted_suites=0,
                                 measured_fail=0, predicted_fail=0, missing=0, denominator=0))
for p in forecast.values():
    key = (p["model"], p["condition"], p["task_family"])
    cell = cells[key]
    cell["suites"] += 1
    cell["denominator"] += 100
    rid = p["run_id"]
    if rid in versions:
        cell["measured_suites"] += 1
        outcomes = Counter(records[(rid, "seeded", s)]["outcome"] for s in range(100))
        cell["measured_fail"] += outcomes["fail"]
        cell["missing"] += outcomes["harness_error"]
    else:
        require(p["prediction_status"] == "clock_only_prediction", f"unrun unpredicted {rid}")
        cell["predicted_suites"] += 1
        cell["predicted_fail"] += p["predicted_failure_count"]

for cell in cells.values():
    lo = (cell["measured_fail"] + cell["predicted_fail"]) / cell["denominator"]
    cell["rate_bound"] = [lo, lo + cell["missing"] / cell["denominator"]]

model_prompt = defaultdict(lambda: dict(suites=0, measured_suites=0, predicted_suites=0,
                                     measured_fail=0, predicted_fail=0, missing=0, denominator=0))
for (model, prompt, _), cell in cells.items():
    target = model_prompt[(model, prompt)]
    for field in target:
        target[field] += cell[field]
for target in model_prompt.values():
    lo = (target["measured_fail"] + target["predicted_fail"]) / target["denominator"]
    target["rate_bound"] = [lo, lo + target["missing"] / target["denominator"]]

suite_distribution = []
for rid, p in sorted(forecast.items()):
    if rid in versions:
        outcomes = Counter(records[(rid, "seeded", s)]["outcome"] for s in range(100))
        suite_distribution.append({"suite_id": rid, "model": p["model"],
                                   "prompt_condition": p["condition"],
                                   "task_family": p["task_family"], "status": "measured",
                                   "fail": outcomes["fail"], "pass": outcomes["pass"],
                                   "missing": outcomes["harness_error"]})
    else:
        suite_distribution.append({"suite_id": rid, "model": p["model"],
                                   "prompt_condition": p["condition"],
                                   "task_family": p["task_family"], "status": "prediction_only",
                                   "predicted_fail": p["predicted_failure_count"]})

contrasts = {}
for model in ("luna", "sol", "astra"):
    families = sorted({key[2] for key in cells if key[0] == model})
    per_family = {}
    for family in families:
        absent = cells[(model, "range_absent", family)]["rate_bound"]
        present = cells[(model, "range_present", family)]["rate_bound"]
        per_family[family] = [present[0] - absent[1], present[1] - absent[0]]
    contrasts[model] = {
        "by_family": per_family,
        "equal_family_bound": [sum(v[j] for v in per_family.values()) / len(per_family)
                               for j in (0, 1)],
    }
pooled = [sum(contrasts[m]["equal_family_bound"][j] for m in contrasts) / len(contrasts)
          for j in (0, 1)]

human = {}
human_ids = {}
for rid, v in versions.items():
    if v["kind"] != "human":
        continue
    human_ids[v["family"]] = rid
    outcomes = Counter(records[(rid, "seeded", s)]["outcome"] for s in range(100))
    human[v["family"]] = dict(fail=outcomes["fail"], missing=outcomes["harness_error"],
                              denominator=100)

paired_cells = defaultdict(Counter)
for p in forecast.values():
    rid = p["run_id"]
    if rid not in versions:
        continue
    key = (p["model"], p["condition"], p["task_family"])
    hid = human_ids[p["task_family"]]
    for seed in range(100):
        ai = records[(rid, "seeded", seed)]["outcome"]
        upstream = records[(hid, "seeded", seed)]["outcome"]
        require(upstream in ("pass", "fail"), f"human verdict missing {hid} seed {seed}")
        paired_cells[key]["AI missing"] += ai == "harness_error"
        if ai in ("pass", "fail"):
            paired_cells[key][f"human {upstream}, AI {ai}"] += 1

summary = {
    "status": "completed_audited",
    "original_records": len(records),
    "seeded_original_records": sum(k[1] == "seeded" for k in records),
    "endpoint_original_records": sum(k[1] != "seeded" for k in records),
    "outcomes": dict(Counter(r["outcome"] for r in records.values())),
    "seeded_outcomes": dict(Counter(r["outcome"] for k, r in records.items() if k[1] == "seeded")),
    "endpoint_outcomes": dict(Counter(r["outcome"] for k, r in records.items() if k[1] != "seeded")),
    "sampled_exact": len(sampled),
    "prediction_only_suites": len(forecast) - len(set(versions) & set(forecast)),
    "persisted_identical_replays": len(replays),
    "classification": dict(Counter(x["classification"] for x in classified.values())),
    "cells": [{"model": k[0], "prompt_condition": k[1], "task_family": k[2], **v}
              for k, v in sorted(cells.items())],
    "model_prompt": [{"model": k[0], "prompt_condition": k[1], **v}
                     for k, v in sorted(model_prompt.items())],
    "suite_distribution": suite_distribution,
    "human": human,
    "paired_measured_cells": [
        {"model": k[0], "prompt_condition": k[1], "task_family": k[2], **dict(v)}
        for k, v in sorted(paired_cells.items())
    ],
    "contrasts": contrasts,
    "equal_model_pooled_contrast_bound": pooled,
    "harness_errors": [{"suite_id": r["suite_id"], "seed": r["seed"],
                        "lsi_frequency_hz": r["lsi_frequency_hz"],
                        "virtual_ns": r["virtual_ns"], "error_type": "Renode monitor timeout"}
                       for k, r in sorted(records.items()) if r["outcome"] == "harness_error"],
}
OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(f"audited {len(records)} originals, {len(sampled)} exact sampled vectors, "
      f"{len(replays)} persisted-identical replays, {len(classified)} classifications")
print(f"summary: {OUT.relative_to(ROOT)}")
