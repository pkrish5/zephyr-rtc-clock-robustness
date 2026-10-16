#!/usr/bin/env python3
"""Registered nominal-host RTC timing fault variants for test-quality checks.

The CPU, SysTick, and test ELF remain frozen. Only the Renode RTC effective
clock is changed outside the legal envelope. Results never enter RQ2 rates.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness/phase3_rtc"))
from run import CASE, MARKERS, RENODE, RenodeSession  # noqa: E402

OUT = ROOT / "results/rtc_timing_mutants_two_faults"
MANIFEST = OUT / "manifest.json"
ORIGINAL_ACTIVATION = ROOT / "results/rtc_timing_mutants/activation_audit.json"
RTC_PLAN = ROOT / "subjects/phase3_rtc/plan.json"
FORECAST = ROOT / "analysis/rtc_threshold_sample_v1/forecast.json"
GATE = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
V2_MANIFEST = ROOT / "results/rtc_factorial_v2/manifest.json"
NOMINAL_PLATFORM = ROOT / "results/phase3_rtc/platforms/stm32f4_rtc_lsi_32000.repl"
REF_MANIFEST = ROOT / "results/rtc_reference_triage_access/manifest.json"
MUTANTS = {"late": 10000, "early": 64000}
MAX_VIRTUAL_SEC = 70


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def register():
    plan, gate, v2 = read(RTC_PLAN), read(GATE), read(V2_MANIFEST)
    activation = read(ORIGINAL_ACTIVATION)
    valid = {(row["family"], row["operator"]) for row in activation["rows"]
             if row.get("activated") is True and row["operator"] in MUTANTS}
    expected = {(family, operator) for family in
                ("rtc_alarm_callback", "rtc_time_counting", "rtc_alarm_pending")
                for operator in MUTANTS}
    if valid != expected:
        raise RuntimeError("Original six early/late reference activations changed")
    eligible = {g["run_id"] for g in gate["rows"]
                if g["amended_functional_eligible"] and g["task_id"].startswith("rtc_")}
    forecast = {p["run_id"]: p for p in read(FORECAST)["predictions"]}
    if eligible != set(forecast) or len(eligible) != 66:
        raise RuntimeError("Eligible RTC task set changed")
    if sha(RTC_PLAN) != v2["schedule_sha256"]:
        raise RuntimeError("RTC schedule changed")
    versions = {}
    for rid, f in sorted(forecast.items()):
        model, condition, family, repeat = rid.split("-", 3)
        build_dir = ROOT / "generated/spec_context_factorial_v1/build" / model / condition / family / repeat
        elf = build_dir / "zephyr/zephyr.elf"
        source = ROOT / f["source_path"]
        if sha(elf) != f["elf_sha256"] or sha(source) != f["source_sha256"]:
            raise RuntimeError(f"Frozen AI artifact changed: {rid}")
        versions[rid] = {"family": family, "kind": "ai", "model": model,
                         "prompt_condition": condition,
                         "source_path": str(source.relative_to(ROOT)),
                         "source_sha256": sha(source),
                         "elf_path": str(elf.relative_to(ROOT)), "elf_sha256": sha(elf)}
    for rid, v in v2["versions"].items():
        if v["kind"] == "human":
            versions[rid] = {k: v[k] for k in ("family", "kind", "model", "prompt_condition",
                                                "source_path", "source_sha256", "elf_path",
                                                "elf_sha256", "selected_case")}
    if len(versions) != 69:
        raise RuntimeError("Expected 66 AI and 3 human suites")
    text = NOMINAL_PLATFORM.read_text()
    if text.count("wakeupTimerFrequency: 32000") != 1:
        raise RuntimeError("Nominal platform RTC field changed")
    platforms = {}
    for name, hz in MUTANTS.items():
        path = OUT / "platforms" / f"rtc_{name}_{hz}.repl"
        path.parent.mkdir(parents=True, exist_ok=True)
        variant = text.replace("wakeupTimerFrequency: 32000", f"wakeupTimerFrequency: {hz}")
        if path.exists():
            if path.read_text() != variant:
                raise RuntimeError(f"Mutant platform changed: {path}")
        else:
            path.write_text(variant)
        platforms[name] = {"effective_rtc_hz": hz, "path": str(path.relative_to(ROOT)),
                           "sha256": sha(path)}
    workers = {str(i): [] for i in range(3)}
    for i, rid in enumerate(sorted(versions)):
        workers[str(i % 3)].append(rid)
    renode_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if renode_version != plan["renode_version"]:
        raise RuntimeError("Renode version changed")
    save_new(MANIFEST, {"registered_utc": stamp(), "schema_version": 1,
                        "intent": "interim two-fault mutation score at nominal host/CPU, outside legal RTC range",
                        "operators": {"late": "10 RTC seconds ideally take 32 host seconds, beyond 17 kHz legal maximum",
                                      "early": "10 RTC seconds ideally take 5 host seconds, earlier than 47 kHz legal minimum"},
                        "max_virtual_sec": MAX_VIRTUAL_SEC, "step_ns": 500000000,
                        "nominal_host_rtc_hz": 32000, "cpu_performance_mips": 16,
                        "systick_frequency_hz": 16000000, "quantum_ns": 1000,
                        "renode_version": renode_version,
                        "source_plan_sha256": sha(RTC_PLAN), "forecast_sha256": sha(FORECAST),
                        "gate_sha256": sha(GATE), "v2_manifest_sha256": sha(V2_MANIFEST),
                        "nominal_platform_sha256": sha(NOMINAL_PLATFORM),
                        "reference_manifest_sha256": sha(REF_MANIFEST),
                        "validated_activation_audit_sha256": sha(ORIGINAL_ACTIVATION),
                        "runner_sha256": sha(Path(__file__)), "platforms": platforms,
                        "versions": versions, "workers": workers})
    print(f"Registered 69 suites × 2 mutants = 138 runs; manifest {sha(MANIFEST)}", flush=True)


def validate():
    m = read(MANIFEST)
    for field, path in (("runner_sha256", Path(__file__)), ("source_plan_sha256", RTC_PLAN),
                        ("forecast_sha256", FORECAST), ("gate_sha256", GATE),
                        ("v2_manifest_sha256", V2_MANIFEST),
                        ("nominal_platform_sha256", NOMINAL_PLATFORM),
                        ("reference_manifest_sha256", REF_MANIFEST),
                        ("validated_activation_audit_sha256", ORIGINAL_ACTIVATION)):
        if sha(path) != m[field]:
            raise RuntimeError(f"Registered input changed: {path}")
    for v in m["versions"].values():
        for field in ("source", "elf"):
            if sha(ROOT / v[f"{field}_path"]) != v[f"{field}_sha256"]:
                raise RuntimeError(f"Frozen {field} changed: {v[field + '_path']}")
    for p in m["platforms"].values():
        if sha(ROOT / p["path"]) != p["sha256"]:
            raise RuntimeError(f"Mutant platform changed: {p['path']}")
    return m


def simulate(m, suite, mutant, activation=False):
    if mutant not in MUTANTS:
        raise ValueError(mutant)
    if activation:
        family = suite
        ref = read(REF_MANIFEST)["reference_builds"][family]
        elf = ROOT / ref["elf_path"]
        source_sha = ref["input_sha256"]
        version = {"family": family, "kind": "reference", "model": "reference",
                   "prompt_condition": None, "selected_case": None}
        run_id = f"activation-{family}-{mutant}"
    else:
        version = m["versions"][suite]
        family = version["family"]
        elf = ROOT / version["elf_path"]
        source_sha = version["source_sha256"]
        run_id = f"{suite}-{mutant}"
    p = m["platforms"][mutant]
    platform = ROOT / p["path"]
    paths = {kind: OUT / folder / f"{run_id}.{ext}" for kind, folder, ext in
             (("record", "activation_records" if activation else "records", "json"),
              ("trace", "activation_traces" if activation else "traces", "json"),
              ("uart", "activation_uart" if activation else "uart", "log"),
              ("monitor", "activation_monitor" if activation else "monitor", "log"))}
    if paths["record"].exists():
        print(f"{run_id}: existing {read(paths['record'])['outcome']}", flush=True)
        return read(paths["record"])
    if any(paths[k].exists() for k in ("trace", "uart", "monitor")):
        raise RuntimeError(f"Incomplete prior mutant artifact: {run_id}")
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    observations, outcome, error, virtual_ns = [], "timeout", None, 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, elf, paths["monitor"]) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{paths['uart']} true")
            for _ in range(2 * m["max_virtual_sec"]):
                session.run_for_ns(m["step_ns"])
                virtual_ns += m["step_ns"]
                output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
                matches = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": matches[-1] if matches else None})
                if any(marker in output for marker in MARKERS):
                    selected = version.get("selected_case")
                    if selected:
                        statuses = [s for s, case in matches if case == selected]
                        outcome = statuses[0].lower() if len(statuses) == 1 else "unknown"
                        if outcome == "unknown":
                            error = f"Selected case verdicts: {statuses}"
                    elif any(s == "FAIL" for s, _ in matches):
                        outcome = "fail"
                    elif matches and all(s == "PASS" for s, _ in matches):
                        outcome = "pass"
                    else:
                        outcome, error = "unknown", "No unambiguous ztest verdict"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
    cases = [{"status": s.lower(), "case": case} for s, case in CASE.findall(output)]
    trace = {"run_id": run_id, "effective_rtc_hz": p["effective_rtc_hz"],
             "observations": observations, "cases": cases, "outcome": outcome,
             "error": error}
    save_new(paths["trace"], trace)
    record = {"run_id": run_id, "family": family, "suite_id": suite,
              "mutant": mutant, "activation": activation, "kind": version["kind"],
              "model": version["model"], "prompt_condition": version["prompt_condition"],
              "nominal_host_rtc_hz": m["nominal_host_rtc_hz"],
              "effective_rtc_hz": p["effective_rtc_hz"],
              "outcome": outcome, "error": error, "cases": cases,
              "virtual_ns": virtual_ns, "wall_seconds": round(time.monotonic()-started, 3),
              "timestamp_utc": stamp(), "manifest_sha256": sha(MANIFEST),
              "source_sha256": source_sha, "elf_sha256": sha(elf),
              "platform_path": p["path"], "platform_sha256": p["sha256"],
              "renode_version": m["renode_version"],
              **{f"{k}_path": str(paths[k].relative_to(ROOT)) for k in
                 ("trace", "uart", "monitor")},
              **{f"{k}_sha256": sha(paths[k]) if paths[k].exists() else None for k in
                 ("trace", "uart", "monitor")}}
    save_new(paths["record"], record)
    print(f"{run_id}: {outcome}, effective RTC={p['effective_rtc_hz']} Hz, "
          f"virtual={virtual_ns/1e9:.1f}s, wall={record['wall_seconds']:.1f}s", flush=True)
    return record


def worker(index):
    m = validate()
    audit = read(ORIGINAL_ACTIVATION)
    valid = {(row["family"], row["operator"]) for row in audit["rows"]
             if row.get("activated") is True and row["operator"] in MUTANTS}
    if len(valid) != 6:
        raise RuntimeError("Two-fault reference activation not validated")
    for rid in m["workers"][str(index)]:
        for mutant in MUTANTS:
            simulate(m, rid, mutant)
    print(f"worker {index}: complete", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--register", action="store_true")
    p.add_argument("--activate", choices=("rtc_alarm_callback", "rtc_time_counting", "rtc_alarm_pending"))
    p.add_argument("--mutant", choices=MUTANTS)
    p.add_argument("--worker", type=int, choices=range(3))
    a = p.parse_args()
    if a.register:
        register()
    elif a.activate and a.mutant:
        simulate(validate(), a.activate, a.mutant, activation=True)
    elif a.worker is not None:
        worker(a.worker)
    else:
        p.error("Specify --register, --activate FAMILY --mutant NAME, or --worker N")


if __name__ == "__main__":
    main()
