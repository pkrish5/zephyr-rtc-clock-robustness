#!/usr/bin/env python3
"""Run frozen upstream Zephyr ztests at recorded, seeded STM32F407 HSI settings."""

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness" / "phase0"))
from session import RenodeSession  # noqa: E402


RESULTS = ROOT / "results" / "phase1"
MANIFEST = json.loads((ROOT / "subjects" / "phase1_zephyr" / "candidates.json").read_text())
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
MIN_HZ, NOMINAL_HZ, MAX_HZ = 15_840_000, 16_000_000, 16_160_000
STEP_NS = 250_000_000
FINAL_MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")
CASE_LINE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def frequency(condition: str, seed: int) -> int:
    if condition == "nominal":
        return NOMINAL_HZ
    if condition == "min":
        return MIN_HZ
    if condition == "max":
        return MAX_HZ
    return random.Random(seed).randint(MIN_HZ, MAX_HZ)


def platform_for(hz: int) -> Path:
    base = RENODE.parent / "platforms" / "cpus" / "stm32f4.repl"
    source = base.read_text()
    needle = "systickFrequency: 72000000"
    if source.count(needle) != 1:
        raise RuntimeError("Renode STM32F4 base platform changed")
    configured = source.replace(needle, f"systickFrequency: {hz}")
    output = RESULTS / "platforms" / f"stm32f4_hsi_{hz}.repl"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.read_text() != configured:
        raise RuntimeError(f"Saved platform changed: {output}")
    if not output.exists():
        output.write_text(configured)
    return output


def append_unique(record: dict):
    output = RESULTS / "runs.jsonl"
    if output.exists():
        existing = {json.loads(line)["run_id"] for line in output.read_text().splitlines()}
        if record["run_id"] in existing:
            raise RuntimeError(f"Duplicate run: {record['run_id']}")
    with output.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def builds_by_id() -> dict:
    path = RESULTS / "builds.jsonl"
    if not path.exists():
        raise RuntimeError("Build the candidate subjects first")
    return {item["subject_id"]: item for item in map(json.loads, path.read_text().splitlines())}


def run_one(subject: dict, build: dict, condition: str, seed: int, max_virtual_sec: int,
            cpu_mips: int, simulator_version: str) -> dict:
    ident = subject["id"]
    run_id = f"{ident}-{condition}-{seed:03d}-mips{cpu_mips}"
    existing = RESULTS / "runs.jsonl"
    if existing.exists() and run_id in {json.loads(line)["run_id"] for line in existing.read_text().splitlines()}:
        raise RuntimeError(f"Run already exists: {run_id}")
    hz = frequency(condition, seed)
    platform = platform_for(hz)
    elf = ROOT / build["elf_path"]
    if sha256(elf) != build["elf_sha256"]:
        raise RuntimeError(f"ELF changed since build: {ident}")
    if source_sha256(ROOT / build["source_path"]) != build["source_tree_sha256"]:
        raise RuntimeError(f"Upstream test source changed since build: {ident}")
    for relative, expected in build["overlay_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"Board overlay changed since build: {relative}")
    uart = RESULTS / "uart_logs" / f"{run_id}.log"
    monitor = RESULTS / "renode_logs" / f"{run_id}.log"
    trace_path = RESULTS / "traces" / f"{run_id}.json"
    for path in (uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite raw output: {path}")
    observations = []
    outcome = "timeout"
    error = None
    start = time.monotonic()
    virtual_ns = 0
    try:
        with RenodeSession(RENODE, platform, elf, monitor) as session:
            session.command(f"cpu PerformanceInMips {cpu_mips}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(max_virtual_sec * 1_000_000_000 // STEP_NS):
                session.run_for_ns(STEP_NS)
                virtual_ns += STEP_NS
                output = uart.read_text(errors="replace") if uart.exists() else ""
                observations.append({
                    "virtual_ns": virtual_ns,
                    "uart_bytes": len(output.encode(errors="replace")),
                    "latest_case": CASE_LINE.findall(output)[-1] if CASE_LINE.findall(output) else None,
                    "completed": any(marker in output for marker in FINAL_MARKERS),
                })
                if FINAL_MARKERS[0] in output:
                    outcome = "pass"
                    break
                if FINAL_MARKERS[1] in output:
                    outcome = "fail"
                    break
    except Exception as exc:
        outcome = "harness_error"
        error = f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": name} for status, name in CASE_LINE.findall(output)]
    trace = {"run_id": run_id, "frequency_hz": hz, "cpu_performance_mips": cpu_mips, "observations": observations,
             "cases": cases, "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "subject_id": ident,
        "condition": condition,
        "seed": seed,
        "frequency_hz": hz,
        "frequency_bound_hz": [MIN_HZ, MAX_HZ],
        "bound_source": "STM32F407 DS8626 Rev 12 Table 34, HSI at 25 C: +/-1%",
        "renode_version": simulator_version,
        "renode_platform_sha256": sha256(platform),
        "renode_platform_path": str(platform.relative_to(ROOT)),
        "quantum_ns": 1000,
        "step_ns": STEP_NS,
        "max_virtual_sec": max_virtual_sec,
        "cpu_performance_mips": cpu_mips,
        "upstream_commit": build["upstream_commit"],
        "source_tree_sha256": build["source_tree_sha256"],
        "elf_sha256": build["elf_sha256"],
        "board_overlay_sha256": build["overlay_sha256"],
        "outcome": outcome,
        "case_counts": {status: sum(item["status"] == status for item in cases) for status in ("pass", "fail", "skip")},
        "virtual_ns": virtual_ns,
        "wall_seconds": round(time.monotonic() - start, 3),
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha256(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "trace_path": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha256(trace_path),
        "error": error,
    }
    append_unique(record)
    print(f"{run_id}: {outcome} cases={record['case_counts']} virtual={virtual_ns/1e9:.2f}s wall={record['wall_seconds']:.1f}s", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", action="append", help="Subject ID; repeat to select multiple")
    parser.add_argument("--condition", choices=["nominal", "perturbed", "min", "max"], required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--max-virtual-sec", type=int, default=30)
    parser.add_argument("--cpu-mips", type=int, default=16)
    args = parser.parse_args()
    if args.start < 0 or args.count < 1 or args.max_virtual_sec < 1 or args.cpu_mips < 1:
        parser.error("start must be nonnegative and count/max-virtual-sec/cpu-mips positive")
    builds = builds_by_id()
    subjects = [item for item in MANIFEST["subjects"] if args.subject is None or item["id"] in args.subject]
    if args.subject and len(subjects) != len(set(args.subject)):
        parser.error("Unknown subject ID")
    simulator_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    for subject in subjects:
        build = builds.get(subject["id"])
        if not build or build["exit_code"] != 0:
            print(f"{subject['id']}: no successful build; retained outside run denominator", flush=True)
            continue
        for seed in range(args.start, args.start + args.count):
            run_id = f"{subject['id']}-{args.condition}-{seed:03d}-mips{args.cpu_mips}"
            records = RESULTS / "runs.jsonl"
            if records.exists() and run_id in {json.loads(line)["run_id"] for line in records.read_text().splitlines()}:
                print(f"{run_id}: already recorded", flush=True)
                continue
            run_one(subject, build, args.condition, seed, args.max_virtual_sec, args.cpu_mips, simulator_version)


if __name__ == "__main__":
    main()
