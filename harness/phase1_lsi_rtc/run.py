#!/usr/bin/env python3
"""Frozen upstream Zephyr RTC suite under seeded, hardware-bounded LSI clocks."""

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

VARIANT = os.environ.get("PHASE1_LSI_VARIANT", "full")
if VARIANT not in ("full", "callback"):
    raise RuntimeError("PHASE1_LSI_VARIANT must be full or callback")
SUBJECT = ROOT / "subjects" / "upstream" / "zephyr" / "tests" / "drivers" / "rtc" / "rtc_api"
ELF = ROOT / "subjects" / "phase1_lsi_rtc" / "build" / ("rtc_api" if VARIANT == "full" else "rtc_alarm_callback") / "zephyr" / "zephyr.elf"
CONFIG = ROOT / "subjects" / "phase1_lsi_rtc"
RESULTS = ROOT / "results" / ("phase1_lsi_rtc" if VARIANT == "full" else "phase1_lsi_alarm")
RUN_PREFIX = "rtc_api" if VARIANT == "full" else "rtc_alarm_callback"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
MIN_HZ, NOMINAL_HZ, MAX_HZ = 17_000, 32_000, 47_000
CASE_LINE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(str(file.relative_to(path)).encode())
        digest.update(bytes.fromhex(sha256(file)))
    return digest.hexdigest()


def freeze() -> dict:
    build_path = RESULTS / "build.json"
    config_files = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay",
                    CONFIG / "rtc_alias.overlay"]
    if VARIANT == "full":
        config_files.append(CONFIG / "rtc_alarm.conf")
    else:
        config_files.extend((CONFIG / "selected_alarm_callback/CMakeLists.txt",
                             CONFIG / "selected_alarm_callback/prj.conf"))
    candidate = {
        "board": "stm32f4_disco/stm32f407xx",
        "upstream_commit": subprocess.check_output(["git", "-C", str(ROOT / "subjects/upstream/zephyr"), "rev-parse", "HEAD"], text=True).strip(),
        "test_source_path": str(SUBJECT.relative_to(ROOT)),
        "test_source_sha256": tree_sha256(SUBJECT),
        "elf_path": str(ELF.relative_to(ROOT)),
        "elf_sha256": sha256(ELF),
        "build_log_sha256": sha256(RESULTS / "build.log"),
        "config_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in config_files},
    }
    if VARIANT == "callback":
        candidate["variant"] = VARIANT
        candidate["linked_upstream_source_sha256"] = {
            str(p.relative_to(ROOT)): sha256(p)
            for p in (SUBJECT / "src/main.c", SUBJECT / "src/test_alarm_callback.c")}
    if build_path.exists():
        saved = json.loads(build_path.read_text())
        if saved != candidate:
            raise RuntimeError("Frozen RTC binary, source, or configuration changed")
        return saved
    build_path.write_text(json.dumps(candidate, sort_keys=True, indent=2) + "\n")
    return candidate


def frequency(condition: str, seed: int) -> int:
    if condition == "nominal":
        return NOMINAL_HZ
    if condition == "min":
        return MIN_HZ
    if condition == "max":
        return MAX_HZ
    return random.Random(seed).randint(MIN_HZ, MAX_HZ)


def platform_for(hz: int) -> Path:
    source = (RENODE.parent / "platforms/cpus/stm32f4.repl").read_text()
    systick = "systickFrequency: 72000000"
    rtc = "rtc: Timers.STM32F4_RTC @ sysbus 0x40002800"
    if source.count(systick) != 1 or source.count(rtc) != 1:
        raise RuntimeError("Pinned Renode STM32F4 platform layout changed")
    configured = source.replace(systick, "systickFrequency: 16000000").replace(
        rtc, rtc + f"\n    wakeupTimerFrequency: {hz}")
    path = RESULTS / "platforms" / f"stm32f4_rtc_lsi_{hz}.repl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != configured:
            raise RuntimeError(f"Saved platform changed: {path}")
    else:
        path.write_text(configured)
    return path


def run_one(condition: str, seed: int, step_ns: int, max_virtual_sec: int, simulator_version: str, build: dict):
    run_id = f"{RUN_PREFIX}-{condition}-{seed:03d}-mips16"
    output_path = RESULTS / "runs.jsonl"
    if output_path.exists() and run_id in {json.loads(line)["run_id"] for line in output_path.read_text().splitlines()}:
        print(f"{run_id}: already recorded", flush=True)
        return
    hz = frequency(condition, seed)
    platform = platform_for(hz)
    uart = RESULTS / "uart_logs" / f"{run_id}.log"
    monitor = RESULTS / "renode_logs" / f"{run_id}.log"
    trace_path = RESULTS / "traces" / f"{run_id}.json"
    for path in (uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite raw artifact: {path}")
    observations = []
    outcome = "timeout"
    error = None
    virtual_ns = 0
    start = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ELF, monitor) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(max_virtual_sec * 1_000_000_000 // step_ns):
                session.run_for_ns(step_ns)
                virtual_ns += step_ns
                output = uart.read_text(errors="replace") if uart.exists() else ""
                matches = CASE_LINE.findall(output)
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
        outcome = "harness_error"
        error = f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": name} for status, name in CASE_LINE.findall(output)]
    trace = {"run_id": run_id, "lsi_frequency_hz": hz, "observations": observations,
             "cases": cases, "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "condition": condition,
        "variant": VARIANT,
        "seed": seed,
        "lsi_frequency_hz": hz,
        "lsi_frequency_bound_hz": [MIN_HZ, MAX_HZ],
        "bound_source": "STM32F407 DS8626 Rev 12 Table 35; LSI 17-47 kHz; VDD 3 V; TA -40 to 105 C",
        "cpu_performance_mips": 16,
        "systick_frequency_hz": 16_000_000,
        "quantum_ns": 1000,
        "step_ns": step_ns,
        "max_virtual_sec": max_virtual_sec,
        "renode_version": simulator_version,
        "renode_platform_path": str(platform.relative_to(ROOT)),
        "renode_platform_sha256": sha256(platform),
        "elf_sha256": build["elf_sha256"],
        "test_source_sha256": build["test_source_sha256"],
        "config_sha256": build["config_sha256"],
        "outcome": outcome,
        "case_counts": {status: sum(c["status"] == status for c in cases) for status in ("pass", "fail", "skip")},
        "virtual_ns": virtual_ns,
        "wall_seconds": round(time.monotonic() - start, 3),
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha256(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "trace_path": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha256(trace_path),
        "error": error,
    }
    with output_path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"{run_id}: {outcome} cases={record['case_counts']} virtual={virtual_ns/1e9:.2f}s wall={record['wall_seconds']:.1f}s", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=("nominal", "perturbed", "min", "max"), required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--step-ms", type=int, default=500)
    parser.add_argument("--max-virtual-sec", type=int, default=150)
    args = parser.parse_args()
    if args.start < 0 or args.count < 1 or args.step_ms < 1 or args.max_virtual_sec < 1:
        parser.error("start must be nonnegative; count, step-ms, and max-virtual-sec must be positive")
    RESULTS.mkdir(parents=True, exist_ok=True)
    build = freeze()
    simulator_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    for seed in range(args.start, args.start + args.count):
        run_one(args.condition, seed, args.step_ms * 1_000_000, args.max_virtual_sec,
                simulator_version, build)


if __name__ == "__main__":
    main()
