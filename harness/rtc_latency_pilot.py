#!/usr/bin/env python3
"""Registered exploratory driver-delay pilot, separate from legal RTC seeds."""

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rtc_quality_build import DRIVER, ROOT, build, create_app, sha, write_new
from rtc_quality_run import PLATFORM, simulate

OUT = ROOT / "results/rtc_latency_pilot"
MANIFEST = OUT / "manifest.json"
V2 = ROOT / "results/rtc_factorial_v2/manifest.json"
CODING = ROOT / "analysis/factorial_latency_assumptions.csv"
BUILD_TOOL = ROOT / "harness/rtc_quality_build.py"
RUN_TOOL = ROOT / "harness/rtc_quality_run.py"
SMOKE_UART = ROOT / "harness/rtc_driver_variants/smoke_app/smoke_uart.log"
SEED = 20261006
LEVELS_US = (0, 1000, 10000, 1000000)
UNKNOWN_QUOTA = {("luna", "range_absent"): 1, ("sol", "range_absent"): 2,
                 ("sol", "range_present"): 3, ("astra", "range_absent"): 2,
                 ("astra", "range_present"): 2}


def read(path):
    return json.loads(path.read_text())


def register():
    v2 = read(V2)
    versions = v2["versions"]
    with CODING.open(newline="") as stream:
        coding = {row["run_id"]: row for row in csv.DictReader(stream)}
    measured_ai = {rid: v for rid, v in versions.items() if v["kind"] == "ai"}
    definite = sorted(rid for rid in measured_ai if
                      coding[rid]["latency_category"] ==
                      "latency_assumption_not_exposed_by_clock_rate")
    unknown = sorted(rid for rid in measured_ai if coding[rid]["latency_category"] == "unknown")
    if len(definite) != 21 or len(unknown) != 23:
        raise RuntimeError(f"Source-coded roster changed: {len(definite)} definite, {len(unknown)} unknown")
    groups = defaultdict(list)
    for rid in unknown:
        v = versions[rid]
        groups[(rid.split("-", 1)[0], v["prompt_condition"])].append(rid)
    if {key: len(value) for key, value in groups.items()} != {
            ("luna", "range_absent"): 1, ("sol", "range_absent"): 3,
            ("sol", "range_present"): 9, ("astra", "range_absent"): 5,
            ("astra", "range_present"): 5}:
        raise RuntimeError("Unknown source-code cells changed")
    rng = random.Random(SEED)
    sampled = sorted(rid for key in sorted(UNKNOWN_QUOTA)
                     for rid in rng.sample(sorted(groups[key]), UNKNOWN_QUOTA[key]))
    human = sorted(rid for rid, v in versions.items() if v["kind"] == "human")
    selected = sorted(definite + sampled + human)
    if len(selected) != 34:
        raise RuntimeError("Pilot must have 21 definite, 10 unknown, and 3 human controls")
    for rid in selected:
        v = versions[rid]
        if sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {rid}")
    workers = {str(i): [] for i in range(3)}
    for i, rid in enumerate(selected):
        workers[str(i % 3)].append(rid)
    smoke = SMOKE_UART.read_text()
    if (smoke.count("QUALITY_DELAY path=alarm request_us=1000") != 2 or
            "PROJECT EXECUTION SUCCESSFUL" not in smoke):
        raise RuntimeError("1 ms isolated-driver smoke evidence missing")
    write_new(MANIFEST, {
        "registered_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1, "intent": "exploratory latency pilot, excluded from legal LSI flip rates",
        "delay_legality": "plausible, not datasheet-legal",
        "mechanism": "isolated STM32 RTC driver: alarm ISR before pending/callback, or first get_time after set_time",
        "levels_us": LEVELS_US, "one_tick_definition": "one RTC calendar second at nominal 32 kHz",
        "random_seed": SEED, "unknown_quota": {"/".join(k): n for k, n in UNKNOWN_QUOTA.items()},
        "definite_ids": definite, "unknown_pool_ids": unknown,
        "sampled_unknown_ids": sampled, "human_control_ids": human,
        "suite_ids": selected, "workers": workers,
        "v2_manifest_sha256": sha(V2), "coding_sha256": sha(CODING),
        "driver_sha256": sha(DRIVER), "builder_sha256": sha(BUILD_TOOL),
        "run_tool_sha256": sha(RUN_TOOL), "runner_sha256": sha(Path(__file__)),
        "platform_sha256": sha(PLATFORM), "smoke_uart_sha256": sha(SMOKE_UART),
        "renode_version": v2["renode_version"], "suite_versions": {rid: versions[rid] for rid in selected},
        "max_virtual_sec": 70, "cpu_performance_mips": 16,
        "reference_tick_smoke_required": True})
    print(f"Registered {len(selected)} suites × {len(LEVELS_US)} levels = 136 runs; "
          f"manifest {sha(MANIFEST)}")


def validate():
    m = read(MANIFEST)
    for key, path in (("v2_manifest_sha256", V2), ("coding_sha256", CODING),
                      ("driver_sha256", DRIVER), ("builder_sha256", BUILD_TOOL),
                      ("run_tool_sha256", RUN_TOOL), ("runner_sha256", Path(__file__)),
                      ("platform_sha256", PLATFORM), ("smoke_uart_sha256", SMOKE_UART)):
        if sha(path) != m[key]:
            raise RuntimeError(f"Registered input changed: {path}")
    for v in m["suite_versions"].values():
        if sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {v['source_path']}")
    return m


def out_for(suite_id, delay_us):
    return OUT / "builds" / suite_id / str(delay_us)


def build_one(m, suite_id, delay_us):
    out = out_for(suite_id, delay_us)
    spec = create_app(out, suite_id, m["suite_versions"], "latency", delay_us)
    return build(out, spec)


def run_one(m, suite_id, delay_us):
    v = m["suite_versions"][suite_id]
    built = build_one(m, suite_id, delay_us)
    if built["status"] != "pass":
        print(f"{suite_id}/{delay_us}: build failure, no simulator verdict", flush=True)
        return
    run_id = f"{suite_id}-{delay_us}us"
    simulate(OUT, run_id, suite_id, v["family"], v["kind"], v.get("selected_case"),
             v["source_sha256"], ROOT / built["elf_path"], MANIFEST,
             max_virtual_sec=m["max_virtual_sec"], delay_us=delay_us)


def tick_smoke():
    m = validate()
    suite_id, delay_us = "reference-rtc_alarm_callback", 1000000
    out = out_for(suite_id, delay_us)
    versions = {suite_id: {"family": "rtc_alarm_callback", "kind": "reference"}}
    spec = create_app(out, suite_id, versions, "latency", delay_us)
    built = build(out, spec)
    if built["status"] != "pass":
        raise RuntimeError("One-tick reference build failed")
    source = ROOT / "subjects/reference_rtc/callback/test.c"
    record = simulate(OUT, f"{suite_id}-{delay_us}us", suite_id,
                      "rtc_alarm_callback", "reference", None, sha(source),
                      ROOT / built["elf_path"], MANIFEST,
                      max_virtual_sec=m["max_virtual_sec"], delay_us=delay_us)
    actual = [x["achieved_us"] for x in record["delay_measurements"]
              if x["path"] == "alarm"]
    validated = (record["outcome"] == "pass" and len(actual) >= 2 and
                 all(900000 <= us <= 1100000 for us in actual))
    write_new(OUT / "tick_smoke_audit.json",
              {"manifest_sha256": sha(MANIFEST), "validated": validated,
               "reference_record_sha256": sha(OUT / "records" /
                                              f"{suite_id}-{delay_us}us.json"),
               "achieved_us": actual})
    print(f"One-tick mechanism validation: {validated}; achieved_us={actual}")


def worker(index, build_only):
    m = validate()
    if not build_only:
        path = OUT / "tick_smoke_audit.json"
        if not path.exists() or read(path)["validated"] is not True:
            raise RuntimeError("One-tick mechanism smoke not validated")
    for rid in m["workers"][str(index)]:
        for level in m["levels_us"]:
            if build_only:
                build_one(m, rid, level)
            else:
                run_one(m, rid, level)
    print(f"pilot {'build' if build_only else 'run'} worker {index}: complete")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--register", action="store_true")
    p.add_argument("--tick-smoke", action="store_true")
    p.add_argument("--build-worker", type=int, choices=range(3))
    p.add_argument("--run-worker", type=int, choices=range(3))
    a = p.parse_args()
    if a.register:
        register()
    elif a.tick_smoke:
        tick_smoke()
    elif a.build_worker is not None:
        worker(a.build_worker, True)
    elif a.run_worker is not None:
        worker(a.run_worker, False)
    else:
        p.error("Specify action")


if __name__ == "__main__":
    main()
