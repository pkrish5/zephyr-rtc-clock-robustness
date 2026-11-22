#!/usr/bin/env python3
"""Summarize a returned, extracted Job A output tree (no firmware).

Usage: analyze_joba.py OUTPUT_DIR --out SUMMARY.json
Reports build status, exact production-compiler mutant counts (compile failures,
TCE equivalents, duplicates), per-app baseline and coverage, timing runs, and the
Job B / Job C recost from measured wall times. Missing outcomes stay missing.
"""
import argparse
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "plan.json").read_text())
MUT = {json.loads(l)["id"]: json.loads(l) for l in (HERE.parents[2] / P["mutants"]).read_text().splitlines()}


def load(p):
    try:
        return json.loads(p.read_text())
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    o = a.output
    apps = P["apps"]
    builds = {x["id"]: load(o / "builds" / x["id"] / "build_record.json") for x in apps}
    tce = {}
    for f in sorted((o / "tce").glob("chunk-*.json")):
        for r in json.loads(f.read_text())["rows"]:
            tce[(r["mutant_id"], r["configuration"])] = r
    first = {}
    for (mid, cfg), r in sorted(tce.items()):
        if r["status"] == "compiled" and not r["tce_equivalent"]:
            r["unique"] = first.setdefault((cfg, r["object_sha256"]), mid) == mid
    tce_summary = {}
    for cfg in ("rtc_alarm", "rtc_counting", "counter"):
        rows = [r for (m, c), r in tce.items() if c == cfg]
        tce_summary[cfg] = dict(
            pairs=len(rows), compile_failure=sum(r["status"] == "compile_failure" for r in rows),
            compile_timeout=sum(r["status"] == "compile_timeout" for r in rows),
            tce_equivalent=sum(r.get("tce_equivalent") is True for r in rows),
            duplicate=sum(r.get("unique") is False for r in rows),
            runnable=sum(r.get("unique") is True for r in rows),
            runnable_by_operator=dict(sorted(Counter(MUT[m]["operator"] for (m, c), r in tce.items()
                                                     if c == cfg and r.get("unique")).items())))
    per_app, covered_runs = {}, {}
    for x in apps:
        b = load(o / "records" / f"{x['id']}-baseline.json")
        t = load(o / "records" / f"{x['id']}-traced.json")
        row = dict(set=x["set"], family=x["family"], build=(builds[x["id"]] or {}).get("status", "missing"),
                   baseline=(b or {}).get("outcome", "missing"), baseline_wall=(b or {}).get("wall_seconds"),
                   traced=(t or {}).get("outcome", "missing"), traced_wall=(t or {}).get("wall_seconds"),
                   tracer_neutral=None, coverage=(t or {}).get("driver_line_coverage"),
                   executed_lines=len((t or {}).get("driver_executed_lines", [])),
                   addressed_lines=len((t or {}).get("driver_addressed_lines", [])),
                   trace_bytes=(t or {}).get("trace_bytes"))
        if b and t:
            row["tracer_neutral"] = b.get("cases") == t.get("cases") and b.get("outcome") == t.get("outcome")
        if t and t.get("driver_executed_lines"):
            ex = set(t["driver_executed_lines"])
            fname = "counter_ll_stm32_rtc.c" if x["driver"] == "counter" else "rtc_ll_stm32.c"
            covered_runs[x["id"]] = sum(1 for (m, c), r in tce.items() if c == x["config"] and r.get("unique")
                                        and MUT[m]["file"] == fname and MUT[m]["line"] in ex)
            row["covered_runnable_mutants"] = covered_runs[x["id"]]
        per_app[x["id"]] = row
    timing = [json.loads(f.read_text()) for f in sorted((o / "timing").glob("*.json"))]
    tw = [t["wall_seconds"] for t in timing if "wall_seconds" in t]
    tb = [t["build_seconds"] for t in timing if "build_seconds" in t]
    by_set = defaultdict(list)
    for k, r in per_app.items():
        if r["coverage"] is not None:
            by_set[r["set"]].append(r["coverage"])
    # Recost Job B: every covered runnable (app, mutant) pair once, measured walls, 32 workers, 1.5 safety.
    rtc_ids = [x["id"] for x in apps if x["driver"] == "rtc"]
    counter_ids = [x["id"] for x in apps if x["driver"] == "counter"]
    mean_run = st.mean(tw) if tw else None
    mean_build = st.mean(tb) if tb else None
    counter_wall = per_app[counter_ids[0]]["baseline_wall"] if counter_ids else None
    rtc_pairs = sum(covered_runs.get(i, 0) for i in rtc_ids)
    counter_pairs = sum(covered_runs.get(i, 0) for i in counter_ids)
    recost = None
    if mean_run and mean_build and counter_wall:
        seconds = rtc_pairs * (mean_run + mean_build) + counter_pairs * (counter_wall + mean_build)
        nh = seconds / P["workers"] / 3600
        recost = dict(rtc_pairs=rtc_pairs, counter_pairs=counter_pairs, mean_rtc_mutant_wall_s=round(mean_run, 1),
                      max_rtc_mutant_wall_s=max(tw), mean_build_s=round(mean_build, 1),
                      counter_baseline_wall_s=counter_wall, job_b_node_hours=round(nh, 2),
                      job_b_su_with_1_5_safety=round(nh * 1.5, 2),
                      note="Assumes timing-sample walls are representative; hung mutants run to their caps.")
    summary = dict(builds=Counter(r["build"] for r in per_app.values()),
                   tce=tce_summary, per_app=per_app,
                   coverage_by_set={k: dict(n=len(v), median=st.median(v), min=min(v), max=max(v))
                                    for k, v in by_set.items()},
                   baselines=Counter(r["baseline"] for r in per_app.values()),
                   tracer_neutral=Counter(str(r["tracer_neutral"]) for r in per_app.values()),
                   timing=dict(runs=len(timing), verdicts=Counter(t.get("verdict", t.get("outcome")) for t in timing)),
                   recost_job_b=recost)
    a.out.write_text(json.dumps(summary, indent=2, sort_keys=True, default=dict) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_app"}, indent=2, sort_keys=True, default=dict))


if __name__ == "__main__":
    main()
