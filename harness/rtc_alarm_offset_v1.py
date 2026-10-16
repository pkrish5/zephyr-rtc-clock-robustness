#!/usr/bin/env python3
"""Preregister and run the nominal-clock RTC-calendar alarm-offset quality arm."""

import argparse
import json
import multiprocessing
from datetime import datetime, timezone
from pathlib import Path

from rtc_alarm_offset_build import DRIVER, REFERENCE, ROOT, build, create_app, sha
from rtc_quality_build import write_new
from rtc_quality_run import PLATFORM, simulate

OUT = ROOT / "results/rtc_alarm_offset_v1"
MANIFEST = OUT / "manifest.json"
V2 = ROOT / "results/rtc_factorial_v2/manifest.json"
GATE = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
BUILDER = ROOT / "harness/rtc_alarm_offset_build.py"
BASE_BUILDER = ROOT / "harness/rtc_quality_build.py"
RUN_TOOL = ROOT / "harness/rtc_quality_run.py"
COMMON = REFERENCE / "reference_common.h"
FAMILIES = ("rtc_alarm_callback", "rtc_alarm_pending", "rtc_time_counting")


def read(path):
    return json.loads(path.read_text())


def register():
    v2 = read(V2)
    gate = read(GATE)
    ai = {row["run_id"] for row in gate["rows"]
          if row["amended_functional_eligible"] and row["task_id"].startswith("rtc_")}
    if len(ai) != 66:
        raise RuntimeError(f"Expected 66 eligible RTC suites, got {len(ai)}")
    old = v2["versions"]
    suites = {k: dict(v) for k, v in old.items() if v["kind"] == "human"}
    for rid in sorted(ai):
        if rid in old:
            suites[rid] = dict(old[rid])
        else:
            model, condition, family, repeat = rid.split("-", 3)
            source = ROOT / "generated/spec_context_factorial_v1/suites" / model / condition / family / repeat / "test.c"
            suites[rid] = {"family": family, "kind": "ai", "model": model,
                           "prompt_condition": condition,
                           "source_path": str(source.relative_to(ROOT)),
                           "source_sha256": sha(source)}
    if len(suites) != 69 or sum(v["family"] != "rtc_time_counting" for v in suites.values()) != 41:
        raise RuntimeError("Expected 69 suites: 41 alarm and 28 counting")
    for family in FAMILIES:
        leaf = {"rtc_alarm_callback": "callback", "rtc_alarm_pending": "pending",
                "rtc_time_counting": "counting"}[family]
        path = REFERENCE / leaf / "test.c"
        suites[f"reference-{family}"] = {
            "family": family, "kind": "reference", "model": "reference",
            "source_path": str(path.relative_to(ROOT)), "source_sha256": sha(path)}
    for rid, v in suites.items():
        if sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Source changed: {rid}")
    scored = sorted(rid for rid in suites if not rid.startswith("reference-"))
    workers = {str(i): scored[i::3] for i in range(3)}
    save = {
        "registered_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
        "purpose": "firmware-level alarm compare offset quality probe; not a legal-clock RQ1 run",
        "operators": {"-1": "program alarm one RTC calendar second early",
                      "+1": "program alarm one RTC calendar second late"},
        "nominal_rtc_hz": 32000, "cpu_performance_mips": 16, "max_virtual_sec": 70,
        "run_order": "nominal reference controls, then both mutant reference activations, then disjoint workers",
        "activation_rule": "at each sign, callback and pending references explicitly fail programmed-alarm readback with a logged requested/programmed RTC-second offset; counting reference passes without alarm programming; nominal references all pass",
        "kill_rule": "For an alarm suite, count a kill only when UART confirms the signed alarm offset activated and the selected ztest case explicitly FAILs. PASS is a survivor; startup/monitor errors or ambiguous cases are missing. An alarm suite with no activation is unscored. Counting suites are nonactivation controls and never enter kill denominators.",
        "replay_rule": "Reexecute explicit kills from identical saved ELF and nominal platform; compare selected-case verdict, error, and offset log; never replace originals",
        "v2_manifest_sha256": sha(V2), "gate_sha256": sha(GATE),
        "driver_sha256": sha(DRIVER), "builder_sha256": sha(BUILDER),
        "base_builder_sha256": sha(BASE_BUILDER), "run_tool_sha256": sha(RUN_TOOL),
        "runner_sha256": sha(Path(__file__)), "reference_common_sha256": sha(COMMON),
        "platform_sha256": sha(PLATFORM), "renode_version": v2["renode_version"],
        "suites": suites, "workers": workers,
    }
    write_new(MANIFEST, save)
    print(f"Registered {len(scored)} suites, 2 offsets, 3 nominal controls: {sha(MANIFEST)}")


def validate():
    m = read(MANIFEST)
    for field, path in (("v2_manifest_sha256", V2), ("gate_sha256", GATE),
                        ("driver_sha256", DRIVER), ("builder_sha256", BUILDER),
                        ("base_builder_sha256", BASE_BUILDER), ("run_tool_sha256", RUN_TOOL),
                        ("runner_sha256", Path(__file__)),
                        ("reference_common_sha256", COMMON), ("platform_sha256", PLATFORM)):
        if sha(path) != m[field]:
            raise RuntimeError(f"Registered input changed: {path}")
    for rid, v in m["suites"].items():
        if sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {rid}")
    return m


def run_suite(suite_id, sign, replay=False):
    m = validate()
    v = m["suites"][suite_id]
    label = f"{suite_id}__{'early' if sign == -1 else 'late' if sign == 1 else 'nominal'}"
    built_dir = OUT / "builds" / label
    spec = create_app(built_dir, suite_id, m["suites"], sign)
    built = build(built_dir, spec)
    if built["status"] != "pass":
        return built
    target = OUT / "replays" if replay else OUT
    run_id = label if not replay else label + "__replay"
    return simulate(target, run_id, suite_id, v["family"], v["kind"],
                    v.get("selected_case"), v["source_sha256"],
                    ROOT / built["elf_path"], MANIFEST, max_virtual_sec=m["max_virtual_sec"])


def audit_activation():
    validate()
    rows = []
    for family in FAMILIES:
        rid = f"reference-{family}"
        for sign in (0, -1, 1):
            label = f"{rid}__{'early' if sign == -1 else 'late' if sign == 1 else 'nominal'}"
            record_path = OUT / "records" / f"{label}.json"
            record = read(record_path)
            uart = (ROOT / record["uart_path"]).read_text(errors="replace")
            alarm = family != "rtc_time_counting"
            if sign == 0 or not alarm:
                valid = record["outcome"] == "pass" and "QUALITY_ALARM_OFFSET id=" not in uart
            else:
                valid = (record["outcome"] == "fail" and
                         "programmed alarm second differs from requested target" in uart and
                         f"QUALITY_ALARM_OFFSET id=0 sign={sign}" in uart)
            rows.append({"run_id": label, "family": family, "sign": sign,
                         "outcome": record["outcome"], "valid": valid,
                         "record_sha256": sha(record_path)})
    status = "validated" if all(r["valid"] for r in rows) else "invalid"
    write_new(OUT / "activation_audit.json", {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha(MANIFEST), "status": status, "rows": rows})
    print(f"Alarm-offset reference activation: {status}")
    return status


def worker(index):
    m = validate()
    if read(OUT / "activation_audit.json")["status"] != "validated":
        raise RuntimeError("Alarm offsets have not passed reference activation")
    for rid in m["workers"][str(index)]:
        for sign in (-1, 1):
            run_suite(rid, sign)
    print(f"worker {index}: complete", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--register", action="store_true")
    p.add_argument("--references", action="store_true")
    p.add_argument("--audit-activation", action="store_true")
    p.add_argument("--workers", action="store_true")
    p.add_argument("--worker", type=int, choices=range(3))
    p.add_argument("--replay-kills", action="store_true")
    a = p.parse_args()
    if a.register:
        register()
    elif a.references:
        for family in FAMILIES:
            for sign in (0, -1, 1):
                run_suite(f"reference-{family}", sign)
    elif a.audit_activation:
        audit_activation()
    elif a.workers:
        procs = [multiprocessing.Process(target=worker, args=(i,)) for i in range(3)]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join()
        if any(proc.exitcode != 0 for proc in procs):
            raise RuntimeError(f"Workers failed: {[p.exitcode for p in procs]}")
    elif a.worker is not None:
        worker(a.worker)
    elif a.replay_kills:
        m = validate()
        for rid in (rid for rid in m["suites"] if not rid.startswith("reference-")):
            if m["suites"][rid]["family"] == "rtc_time_counting":
                continue
            for sign in (-1, 1):
                label = f"{rid}__{'early' if sign == -1 else 'late'}"
                path = OUT / "records" / f"{label}.json"
                if not path.exists():
                    continue
                record = read(path)
                uart = (ROOT / record["uart_path"]).read_text(errors="replace")
                if record["outcome"] == "fail" and f"QUALITY_ALARM_OFFSET id=" in uart:
                    run_suite(rid, sign, replay=True)
    else:
        p.error("Choose an action")


if __name__ == "__main__":
    main()
