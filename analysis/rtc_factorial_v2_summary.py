#!/usr/bin/env python3
"""Read-only progress and final-rate summary for the locked RTC v2 arm."""

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_factorial_v2"
MANIFEST = json.loads((BASE / "manifest.json").read_text())
FORECAST = json.loads((ROOT / "analysis/rtc_threshold_sample_v1/forecast.json").read_text())
SAMPLE = json.loads((ROOT / "analysis/rtc_threshold_sample_v2/sample.json").read_text())


def wilson(fail, n):
    if not n:
        return None
    z = 1.959963984540054
    p = fail / n
    d = 1 + z*z/n
    center = (p + z*z/(2*n)) / d
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [round(center-half, 4), round(center+half, 4)]


records = {}
for path in (BASE / "records").glob("*.json") if (BASE / "records").exists() else []:
    row = json.loads(path.read_text())
    key = (row["suite_id"], row["condition"], row["seed"])
    if key in records:
        raise RuntimeError(f"Duplicate original result {key}")
    records[key] = row

forecast = {p["run_id"]: p for p in FORECAST["predictions"]}
sampled = set(SAMPLE["sampled_predictable_run_ids"])
print("original records", len(records), "seeded", sum(k[1] == "seeded" for k in records),
      "endpoint", sum(k[1] != "seeded" for k in records))
stop = BASE / "STOP_PREDICTION_MISMATCH.json"
if stop.exists():
    print("PREDICTION MISMATCH STOP", json.dumps(json.loads(stop.read_text()), sort_keys=True))

split = defaultdict(Counter)
for p in forecast.values():
    split[(p["model"], p["condition"])][p["prediction_status"]] += 1
print("\npredictability (frozen source review; predictable / not predictable)")
for key in sorted(split):
    c = split[key]
    print(*key, c["clock_only_prediction"], c["not_predictable"])

print("\nper measured suite (failure/evaluable/missing/remaining; Wilson 95% on evaluable only)")
for rid, v in sorted(MANIFEST["versions"].items(), key=lambda kv: (kv[1]["family"], kv[1]["kind"], kv[1]["model"], str(kv[1]["prompt_condition"]), kv[0])):
    xs = [records[(rid, "seeded", s)] for s in range(100) if (rid, "seeded", s) in records]
    c = Counter(x["outcome"] for x in xs)
    ev = c["pass"] + c["fail"]
    disagree = []
    if rid in sampled:
        pred = set(v["predicted_failure_seeds"])
        disagree = [x["seed"] for x in xs if x["outcome"] in ("pass", "fail") and (x["outcome"] == "fail") != (x["seed"] in pred)]
    print(rid, f"{c['fail']}/{ev}", f"missing={len(xs)-ev}", f"remaining={100-len(xs)}", f"CI={wilson(c['fail'],ev)}", f"mismatch={disagree}")

print("\nmeasured cells (human alongside AI by family)")
cells = defaultdict(list)
for rid, v in MANIFEST["versions"].items():
    cells[(v["family"], v["model"], v["prompt_condition"])].append(rid)
for (family, model, condition), ids in sorted(cells.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
    xs = [records[(rid, "seeded", s)] for rid in ids for s in range(100) if (rid, "seeded", s) in records]
    c = Counter(x["outcome"] for x in xs)
    ev = c["pass"] + c["fail"]
    print(family, model, condition or "-", f"suites={len(ids)}", f"fail={c['fail']}/{ev}",
          f"missing={len(xs)-ev}", f"remaining={100*len(ids)-len(xs)}", f"CI={wilson(c['fail'],ev)}")

complete = all((rid, "seeded", s) in records for rid in MANIFEST["versions"] for s in range(100))
validated = complete and all(
    all(records[(rid, "seeded", s)]["outcome"] in ("pass", "fail") and
        (records[(rid, "seeded", s)]["outcome"] == "fail") == (s in set(MANIFEST["versions"][rid]["predicted_failure_seeds"]))
        for s in range(100)) for rid in sampled)
print("\nall measured seed records complete", complete, "sample validation exact and evaluable", validated)
if complete and validated:
    print("\nhybrid all-eligible model/prompt/family cells (measured and predicted kept separate)")
    grouped = defaultdict(list)
    for p in forecast.values():
        grouped[(p["model"], p["condition"], p["task_family"])].append(p)
    for key, ps in sorted(grouped.items()):
        measured_fail = measured_pass = missing = predicted_fail = predicted_pass = 0
        for p in ps:
            rid = p["run_id"]
            if rid in MANIFEST["versions"]:
                for s in range(100):
                    outcome = records[(rid, "seeded", s)]["outcome"]
                    measured_fail += outcome == "fail"
                    measured_pass += outcome == "pass"
                    missing += outcome not in ("pass", "fail")
            else:
                predicted_fail += p["predicted_failure_count"]
                predicted_pass += 100 - p["predicted_failure_count"]
        total = 100 * len(ps)
        print(*key, f"measured_fail={measured_fail}", f"predicted_fail={predicted_fail}",
              f"missing={missing}", f"denominator={total}",
              f"bounds=[{(measured_fail+predicted_fail)/total:.4f},{(measured_fail+predicted_fail+missing)/total:.4f}]")
