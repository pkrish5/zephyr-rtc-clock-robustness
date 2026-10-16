#!/usr/bin/env python3
"""Build frozen agent suites and run each built ELF once at nominal timing."""

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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness/phase0"))
from session import RenodeSession  # noqa: E402

COHORT = os.environ.get("PHASE2_COHORT", "sol_pilot")
COHORT_PATHS = {
    "sol_pilot": ("subjects/phase2_tasks.json", "phase2"),
    "luna_primary": ("subjects/phase2_tasks.json", "phase2_luna"),
    "rtc_bound_supplement": ("subjects/phase2_rtc_bound_tasks.json", "phase2_rtc_bound"),
    "sol_comparison": ("subjects/phase2_tasks_v2.json", "phase2_sol_comparison"),
    "astra_comparison": ("subjects/phase2_tasks_v2.json", "phase2_astra_comparison"),
    "luna_rtc_extension": ("subjects/rtc_extension_tasks.json", "luna_rtc_extension"),
}
if COHORT not in COHORT_PATHS:
    raise RuntimeError(f"Unknown Phase 2 cohort: {COHORT}")
task_file, cohort_directory = COHORT_PATHS[COHORT]
TASKS = ROOT / task_file
GENERATED = ROOT / "generated" / cohort_directory
RESULTS = ROOT / "results" / cohort_directory
BUILDS = GENERATED / "build"
WEST = ROOT / ".venv/bin/west"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_new(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def existing_ids(path: Path) -> set[str]:
    return {json.loads(line)["run_id"] for line in path.read_text().splitlines()} if path.exists() else set()


def configure(task: dict, run_dir: Path) -> dict:
    cmake = run_dir / "CMakeLists.txt"
    conf = run_dir / "prj.conf"
    content = ("cmake_minimum_required(VERSION 3.20.0)\n"
               "find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})\n"
               f"project(generated_{task['id']})\n"
               "target_sources(app PRIVATE test.c)\n")
    for path, expected in ((cmake, content), (conf, task["build_conf"])):
        if path.exists():
            if path.read_text() != expected:
                raise RuntimeError(f"Study-owned build configuration changed: {path}")
        else:
            path.write_text(expected)
    overlays = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay"]
    if task["arm"] == "lsi_pilot":
        overlays.append(ROOT / "subjects/phase1_lsi_rtc/rtc_alias.overlay")
    return {"cmake_sha256": sha256(cmake), "prj_conf_sha256": sha256(conf),
            "overlay_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in overlays},
            "overlays": overlays}


def build_one(task: dict, index: int) -> dict | None:
    run_id = f"{task['id']}-r{index:02d}"
    prior = RESULTS / "builds.jsonl"
    if run_id in existing_ids(prior):
        return next(json.loads(line) for line in prior.read_text().splitlines() if json.loads(line)["run_id"] == run_id)
    run_dir = GENERATED / "suites" / task["id"] / f"r{index:02d}"
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    generation = json.loads(metadata_path.read_text())
    if generation["status"] != "generated":
        return None
    source = run_dir / "test.c"
    if sha256(source) != generation["source_sha256"]:
        raise RuntimeError(f"Generated source changed: {run_id}")
    config = configure(task, run_dir)
    build_dir = BUILDS / task["id"] / f"r{index:02d}"
    log = RESULTS / "build_logs" / f"{run_id}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        raise RuntimeError(f"Unrecorded build log exists: {run_id}")
    env = os.environ.copy()
    env.setdefault("ZEPHYR_BASE", str(ROOT / "subjects/upstream/zephyr"))
    env.setdefault("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/phase1-zephyr-sdk")
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    cmd = [str(WEST), "build", "-p", "always", "-b", "stm32f4_disco",
           str(run_dir), "-d", str(build_dir), "--",
           "-DDTC_OVERLAY_FILE=" + ";".join(str(p) for p in config["overlays"])]
    start = time.monotonic()
    try:
        with log.open("w") as stream:
            process = subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT, env=env,
                                     timeout=600, check=False)
        returncode, timed_out = process.returncode, False
    except subprocess.TimeoutExpired:
        returncode, timed_out = None, True
    elf = build_dir / "zephyr/zephyr.elf"
    status = "pass" if returncode == 0 and elf.exists() else "timeout" if timed_out else "fail"
    record = {
        "run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status, "returncode": returncode,
        "wall_seconds": round(time.monotonic() - start, 3),
        "generation_metadata_sha256": sha256(metadata_path),
        "prompt_sha256": generation["prompt_sha256"],
        "source_sha256": generation["source_sha256"],
        "cmake_sha256": config["cmake_sha256"],
        "prj_conf_sha256": config["prj_conf_sha256"],
        "overlay_sha256": config["overlay_sha256"],
        "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
        "elf_sha256": sha256(elf) if elf.exists() else None,
        "build_log_path": str(log.relative_to(ROOT)), "build_log_sha256": sha256(log),
        "zephyr_commit": json.loads(TASKS.read_text())["zephyr_commit"],
    }
    append_new(prior, record)
    print(f"{run_id}: build {status}", flush=True)
    return record


def nominal_one(task: dict, build: dict) -> None:
    run_id = build["run_id"]
    prior = RESULTS / "nominal_runs.jsonl"
    if run_id in existing_ids(prior) or build["status"] != "pass":
        return
    platform = ROOT / ("results/phase1_lsi_alarm/platforms/stm32f4_rtc_lsi_32000.repl"
                       if task["arm"] == "lsi_pilot" else
                       "results/phase1/platforms/stm32f4_hsi_16000000.repl")
    elf = ROOT / build["elf_path"]
    if sha256(elf) != build["elf_sha256"]:
        raise RuntimeError(f"Frozen ELF changed: {run_id}")
    uart = RESULTS / "nominal_uart" / f"{run_id}.log"
    monitor = RESULTS / "nominal_monitor" / f"{run_id}.log"
    trace_path = RESULTS / "nominal_traces" / f"{run_id}.json"
    for path in (uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"Unrecorded nominal artifact exists: {path}")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    observations = []
    outcome = "timeout"
    error = None
    max_sec = 60 if task["arm"] == "lsi_pilot" else 90
    step_ns = 500_000_000
    virtual_ns = 0
    start = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, elf, monitor) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(max_sec * 2):
                session.run_for_ns(step_ns)
                virtual_ns += step_ns
                output = uart.read_text(errors="replace") if uart.exists() else ""
                matches = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": list(matches[-1]) if matches else None,
                                     "completed": any(marker in output for marker in MARKERS)})
                if MARKERS[0] in output:
                    outcome = "pass"
                    break
                if MARKERS[1] in output:
                    outcome = "fail"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": case} for status, case in CASE.findall(output)]
    trace = {"run_id": run_id, "condition": "nominal", "seed": 0,
             "outcome": outcome, "cases": cases, "observations": observations, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    record = {
        "run_id": run_id, "condition": "nominal", "seed": 0,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome, "cases": cases, "error": error,
        "virtual_ns": virtual_ns, "wall_seconds": round(time.monotonic() - start, 3),
        "elf_sha256": build["elf_sha256"], "source_sha256": build["source_sha256"],
        "prompt_sha256": build["prompt_sha256"],
        "renode_version": version, "platform_path": str(platform.relative_to(ROOT)),
        "platform_sha256": sha256(platform), "cpu_performance_mips": 16,
        "systick_frequency_hz": 16_000_000,
        "lsi_frequency_hz": 32_000 if task["arm"] == "lsi_pilot" else None,
        "quantum_ns": 1000, "step_ns": step_ns, "max_virtual_sec": max_sec,
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha256(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "trace_path": str(trace_path.relative_to(ROOT)), "trace_sha256": sha256(trace_path),
    }
    append_new(prior, record)
    print(f"{run_id}: nominal {outcome}, cases={len(cases)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", help="One registered task")
    parser.add_argument("--index", type=int, help="One sample index 1..5")
    parser.add_argument("--skip-nominal", action="store_true")
    args = parser.parse_args()
    tasks = json.loads(TASKS.read_text())["tasks"]
    if args.task and args.task not in {t["id"] for t in tasks}:
        parser.error("Unknown task")
    if args.index and args.index not in range(1, 6):
        parser.error("Index must be 1..5")
    for task in tasks:
        if args.task and task["id"] != args.task:
            continue
        for index in ([args.index] if args.index else range(1, 6)):
            built = build_one(task, index)
            if built and not args.skip_nominal:
                nominal_one(task, built)


if __name__ == "__main__":
    main()
