#!/usr/bin/env python3
"""Registered RTC v2 suite-disjoint workers, with per-seed prediction checks."""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness/phase3_rtc"))
from run import CASE, MARKERS, RENODE, RenodeSession, path_for, sha256  # noqa: E402

OUT = ROOT / "results/rtc_factorial_v2"
SAMPLE = ROOT / "analysis/rtc_threshold_sample_v2/sample.json"
FORECAST = ROOT / "analysis/rtc_threshold_sample_v1/forecast.json"
SCHEDULE = ROOT / "subjects/phase3_rtc/plan.json"
GATE = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
REPORT = ROOT / "analysis/rtc_threshold_sample_v2/predictability_report.csv"
MANIFEST = OUT / "manifest.json"
STOP = OUT / "STOP_PREDICTION_MISMATCH.json"

HUMAN = {
    "human-rtc_alarm_callback": ("rtc_alarm_callback", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c", "subjects/phase1_lsi_rtc/build/rtc_alarm_callback/zephyr/zephyr.elf", "rtc_api.test_alarm_callback"),
    "human-rtc_time_counting": ("rtc_time_counting", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_time_incrementing.c", "subjects/rtc_counting/build/selected_case/zephyr/zephyr.elf", "rtc_api.test_time_counting"),
    "human-rtc_alarm_pending": ("rtc_alarm_pending", "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm.c", "subjects/rtc_alarm_pending/build/selected_case/zephyr/zephyr.elf", "rtc_api.test_alarm"),
}


def read(path):
    return json.loads(path.read_text())


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def build_record(rid):
    base = ROOT / "results/spec_context_factorial_v1"
    retry = base / "build_retry_records" / f"{rid}.json"
    return read(retry if retry.exists() else base / "build_records" / f"{rid}.json")


def init():
    sample, forecast, schedule, gate = map(read, (SAMPLE, FORECAST, SCHEDULE, GATE))
    if sha256(FORECAST) != sample["forecast_sha256"]:
        raise RuntimeError("v2 sample forecast hash mismatch")
    original_lock = read(ROOT / "analysis/rtc_threshold_sample_v2/lock.json")
    if sha256(SAMPLE) != original_lock["sample_sha256"]:
        raise RuntimeError("v2 sample lock mismatch")
    forecast_by_id = {p["run_id"]: p for p in forecast["predictions"]}
    gate_by_id = {g["run_id"]: g for g in gate["rows"]}
    if set(forecast_by_id) != {g["run_id"] for g in gate["rows"] if g["amended_functional_eligible"] and g["task_id"].startswith("rtc_")}:
        raise RuntimeError("Forecast and eligible RTC gate sets differ")
    selected = set(sample["all_phase3_measured_run_ids"])
    if selected != set(sample["sampled_predictable_run_ids"]) | set(sample["full_run_not_predictable_run_ids"]):
        raise RuntimeError("v2 measured split changed")
    if len(selected) != 50 or len(sample["unsampled_prediction_only_run_ids"]) != 16:
        raise RuntimeError("v2 sample size changed")
    with REPORT.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["run_id", "model", "prompt_condition", "task_family", "predictability", "reason", "measured_role"])
        writer.writeheader()
        for rid, p in sorted(forecast_by_id.items()):
            role = "sampled_predictable" if rid in sample["sampled_predictable_run_ids"] else "full_not_predictable" if rid in sample["full_run_not_predictable_run_ids"] else "prediction_only"
            writer.writerow({"run_id": rid, "model": p["model"], "prompt_condition": p["condition"], "task_family": p["task_family"], "predictability": p["prediction_status"], "reason": p["prediction_reason"], "measured_role": role})
    versions = {}
    for rid in sorted(selected):
        p, g, b = forecast_by_id[rid], gate_by_id[rid], build_record(rid)
        if not g["amended_functional_eligible"] or b["status"] != "pass":
            raise RuntimeError(f"Gate/build exclusion changed: {rid}")
        if b["source_sha256"] != p["source_sha256"] or b["elf_sha256"] != p["elf_sha256"]:
            raise RuntimeError(f"Forecast/build hash mismatch: {rid}")
        if sha256(ROOT / b["source_path"]) != p["source_sha256"] or sha256(ROOT / b["elf_path"]) != p["elf_sha256"]:
            raise RuntimeError(f"Frozen artifact changed: {rid}")
        versions[rid] = {"kind": "ai", "family": p["task_family"], "model": p["model"], "prompt_condition": p["condition"], "role": "sampled_predictable" if rid in sample["sampled_predictable_run_ids"] else "full_not_predictable", "source_path": b["source_path"], "source_sha256": p["source_sha256"], "elf_path": b["elf_path"], "elf_sha256": p["elf_sha256"], "predicted_failure_seeds": p["predicted_failure_seeds"]}
    for rid, (family, source, elf, case) in HUMAN.items():
        versions[rid] = {"kind": "human", "family": family, "model": "human", "prompt_condition": None, "role": "human_full", "source_path": source, "source_sha256": sha256(ROOT / source), "elf_path": elf, "elf_sha256": sha256(ROOT / elf), "selected_case": case, "predicted_failure_seeds": None}
    # Each worker owns complete suites. Sampled cases precede not-predictable cases.
    sampled = sorted(sample["sampled_predictable_run_ids"], key=lambda x: (-len(versions[x]["predicted_failure_seeds"]), x))
    early = sampled + sorted(HUMAN)
    late = sorted(sample["full_run_not_predictable_run_ids"])
    workers = {str(i): [] for i in range(3)}
    for group in (early, late):
        for j, rid in enumerate(group):
            workers[str(j % 3)].append(rid)
    if set(sum(workers.values(), [])) != set(versions) or len(sum(workers.values(), [])) != len(versions):
        raise RuntimeError("Worker partition overlaps or omits a suite")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if version != schedule["renode_version"]:
        raise RuntimeError("Renode version differs from registered RTC schedule")
    for hz in {*schedule["seeded_frequencies_hz"], 17000, 47000}:
        path_for(hz)  # validate that saved platform bytes still match
    manifest = {"registered_utc": utc(), "schema_version": 1, "worker_count": 3,
                "host_logical_cpus": os.cpu_count(), "workers": workers, "versions": versions,
                "runner_sha256": sha256(Path(__file__)), "sample_sha256": sha256(SAMPLE),
                "forecast_sha256": sha256(FORECAST), "schedule_sha256": sha256(SCHEDULE),
                "gate_sha256": sha256(GATE), "predictability_report_sha256": sha256(REPORT),
                "renode_version": version, "schedule_seeds": 100, "endpoints": ["min", "max"],
                "max_concurrent_renode_processes": 3,
                "worker_partition_rule": "disjoint whole suites; every suite uses paired seeds 0..99"}
    write_new(MANIFEST, manifest)
    print(f"Registered {len(versions)} measured suites, 3 workers, manifest SHA-256 {sha256(MANIFEST)}")


def validate():
    m = read(MANIFEST)
    for key, path in (("runner_sha256", Path(__file__)), ("sample_sha256", SAMPLE), ("forecast_sha256", FORECAST), ("schedule_sha256", SCHEDULE), ("gate_sha256", GATE), ("predictability_report_sha256", REPORT)):
        if sha256(path) != m[key]:
            raise RuntimeError(f"Locked input changed: {path}")
    for rid, v in m["versions"].items():
        for key in ("source", "elf"):
            if sha256(ROOT / v[f"{key}_path"]) != v[f"{key}_sha256"]:
                raise RuntimeError(f"Frozen {key} changed: {rid}")
    return m, read(SCHEDULE)


def simulate(m, schedule, rid, condition, index, replay=False):
    v = m["versions"][rid]
    hz = schedule["seeded_frequencies_hz"][index] if condition == "seeded" else schedule["endpoints_hz"][condition]
    run_id = f"{rid}-{condition}-{index:03d}" if condition == "seeded" else f"{rid}-{condition}"
    prefix = "replay_" if replay else ""
    paths = {k: OUT / f"{prefix}{directory}" / f"{run_id}.{ext}" for k, directory, ext in (("record", "records", "json"), ("uart", "uart", "log"), ("monitor", "monitor", "log"), ("trace", "traces", "json"))}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    if paths["record"].exists():
        old = read(paths["record"])
        if old["manifest_sha256"] != sha256(MANIFEST):
            raise RuntimeError(f"Existing record lock mismatch: {run_id}")
        return old
    if any(paths[k].exists() for k in ("uart", "monitor", "trace")):
        raise RuntimeError(f"Refusing overwrite of incomplete artifacts: {run_id}")
    platform = path_for(hz)
    outcome, error, virtual_ns = "timeout", None, 0
    observations = []
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ROOT / v["elf_path"], paths["monitor"]) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{paths['uart']} true")
            for _ in range(schedule["max_virtual_sec"] * 1_000_000_000 // schedule["step_ns"]):
                session.run_for_ns(schedule["step_ns"])
                virtual_ns += schedule["step_ns"]
                output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
                matches = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns, "uart_bytes": len(output.encode(errors="replace")), "latest_case": matches[-1] if matches else None, "completed": any(x in output for x in MARKERS)})
                if any(x in output for x in MARKERS):
                    if v["kind"] == "human":
                        selected = [s for s, case in matches if case == v["selected_case"]]
                        if len(selected) == 1:
                            outcome = selected[0].lower()
                        else:
                            outcome, error = "unknown", f"Expected one selected case verdict, got {selected}"
                    elif not matches:
                        outcome, error = "unknown", "No ztest case verdict"
                    elif any(s == "FAIL" for s, _ in matches):
                        outcome = "fail"
                    elif "PROJECT EXECUTION FAILED" in output:
                        outcome, error = "unknown", "Project failure without failing case"
                    elif all(s == "PASS" for s, _ in matches):
                        outcome = "pass"
                    else:
                        outcome, error = "unknown", "Skipped or unclassified case"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
    cases = [{"status": s.lower(), "case": c} for s, c in CASE.findall(output)]
    trace = {"run_id": run_id, "condition": condition, "seed": index if condition == "seeded" else None,
             "lsi_frequency_hz": hz, "observations": observations, "cases": cases,
             "outcome": outcome, "error": error}
    write_new(paths["trace"], trace)
    record = {"run_id": run_id, "suite_id": rid, "kind": v["kind"], "family": v["family"],
              "model": v["model"], "prompt_condition": v["prompt_condition"], "role": v["role"],
              "timestamp_utc": utc(), "condition": condition, "seed": index if condition == "seeded" else None,
              "lsi_frequency_hz": hz, "outcome": outcome, "error": error, "cases": cases,
              "virtual_ns": virtual_ns, "wall_seconds": round(time.monotonic()-started, 3),
              "cpu_performance_mips": 16, "systick_frequency_hz": 16000000,
              "quantum_ns": 1000, "step_ns": schedule["step_ns"], "max_virtual_sec": schedule["max_virtual_sec"],
              "source_sha256": v["source_sha256"], "elf_sha256": v["elf_sha256"],
              "platform_path": str(platform.relative_to(ROOT)), "platform_sha256": sha256(platform),
              "renode_version": m["renode_version"], "manifest_sha256": sha256(MANIFEST),
              "schedule_sha256": m["schedule_sha256"],
              **{f"{k}_path": str(paths[k].relative_to(ROOT)) for k in ("uart", "monitor", "trace")},
              **{f"{k}_sha256": sha256(paths[k]) if paths[k].exists() else None for k in ("uart", "monitor", "trace")}}
    if replay:
        original = read(OUT / "records" / f"{run_id}.json")
        prior = read(ROOT / original["trace_path"])
        record["original_trace_sha256"] = original["trace_sha256"]
        record["identical_trace_and_verdict"] = all(trace[k] == prior[k] for k in ("lsi_frequency_hz", "observations", "cases", "outcome", "error"))
    write_new(paths["record"], record)
    print(f"{run_id}{' REPLAY' if replay else ''}: {outcome}, LSI={hz}, wall={record['wall_seconds']:.1f}s", flush=True)
    return record


def worker(index):
    m, schedule = validate()
    for rid in m["workers"][str(index)]:
        v = m["versions"][rid]
        print(f"worker {index}: suite {rid}", flush=True)
        for condition, n in (("seeded", 100), ("min", 1), ("max", 1)):
            for seed in range(n):
                if STOP.exists():
                    print(f"worker {index}: stopped by prediction mismatch", flush=True)
                    return
                record = simulate(m, schedule, rid, condition, seed)
                if condition == "seeded" and v["role"] == "sampled_predictable" and record["outcome"] in ("pass", "fail"):
                    predicted = "fail" if seed in v["predicted_failure_seeds"] else "pass"
                    if record["outcome"] != predicted:
                        # Exclusive create makes the first mismatch authoritative.
                        try:
                            write_new(STOP, {"timestamp_utc": utc(), "run_id": record["run_id"], "suite_id": rid,
                                             "seed": seed, "lsi_frequency_hz": record["lsi_frequency_hz"],
                                             "predicted": predicted, "observed": record["outcome"],
                                             "record_sha256": sha256(OUT / "records" / f"{record['run_id']}.json")})
                        except FileExistsError:
                            pass
                if record["outcome"] == "fail":
                    replay = simulate(m, schedule, rid, condition, seed, replay=True)
                    ledger = {"run_id": record["run_id"], "original_outcome": "fail",
                              "replay_outcome": replay["outcome"],
                              "replay_identical": replay["identical_trace_and_verdict"],
                              "classification": "unknown",
                              "reason": "Fresh-process replay completed; source and firmware-cause adjudication pending. Preserve unknown until ruled in by evidence."}
                    write_new(OUT / "classification" / f"{record['run_id']}.json", ledger)
                if STOP.exists():
                    print(f"worker {index}: stopped after {record['run_id']}", flush=True)
                    return
    print(f"worker {index}: complete", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--init", action="store_true")
    p.add_argument("--worker", type=int, choices=range(3))
    a = p.parse_args()
    if a.init:
        init()
    elif a.worker is not None:
        worker(a.worker)
    else:
        p.error("Specify --init or --worker 0/1/2")


if __name__ == "__main__":
    main()
