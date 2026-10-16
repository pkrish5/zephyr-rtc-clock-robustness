#!/usr/bin/env python3
"""Fresh-process replay of an immutable Phase 1 run record."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness" / "phase0"))
from session import RenodeSession  # noqa: E402


RESULTS = ROOT / "results" / "phase1"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
CASE_LINE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")


def runs() -> dict:
    return {item["run_id"]: item for item in map(json.loads, (RESULTS / "runs.jsonl").read_text().splitlines())}


def replay(original: dict):
    run_id = original["run_id"]
    prior_path = RESULTS / "replays.jsonl"
    if prior_path.exists() and run_id in {json.loads(line)["run_id"] for line in prior_path.read_text().splitlines()}:
        print(f"{run_id}: already replayed", flush=True)
        return
    uart = RESULTS / "replay_logs" / f"{run_id}.uart.log"
    monitor = RESULTS / "replay_logs" / f"{run_id}.monitor.log"
    uart.parent.mkdir(parents=True, exist_ok=True)
    if uart.exists() or monitor.exists():
        raise RuntimeError(f"Raw replay output already exists: {run_id}")
    elf = ROOT / next(item["elf_path"] for item in map(json.loads, (RESULTS / "builds.jsonl").read_text().splitlines()) if item["subject_id"] == original["subject_id"])
    import hashlib
    if hashlib.sha256(elf.read_bytes()).hexdigest() != original["elf_sha256"]:
        raise RuntimeError(f"ELF changed: {run_id}")
    platform_path = ROOT / original["renode_platform_path"]
    if hashlib.sha256(platform_path.read_bytes()).hexdigest() != original["renode_platform_sha256"]:
        raise RuntimeError(f"Renode platform changed: {run_id}")
    simulator_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if simulator_version != original["renode_version"]:
        raise RuntimeError(f"Renode version changed: {run_id}")
    step_ns = original.get("step_ns", 250_000_000)
    max_virtual_sec = original.get("max_virtual_sec", 90)
    outcome = "timeout"
    observations = []
    error = None
    try:
        with RenodeSession(RENODE, platform_path, elf, monitor) as session:
            session.command(f"cpu PerformanceInMips {original['cpu_performance_mips']}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for step in range(1, max_virtual_sec * 1_000_000_000 // step_ns + 1):
                session.run_for_ns(step_ns)
                output = uart.read_text(errors="replace") if uart.exists() else ""
                matches = CASE_LINE.findall(output)
                observations.append({"virtual_ns": step * step_ns,
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
    original_trace = json.loads((ROOT / original["trace_path"]).read_text())
    identical = outcome == original_trace["outcome"] and cases == original_trace["cases"] and observations == original_trace["observations"]
    record = {"run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "identical_trace_and_verdict": identical, "outcome": outcome,
              "original_trace_path": original["trace_path"],
              "uart_path": str(uart.relative_to(ROOT)), "monitor_path": str(monitor.relative_to(ROOT)),
              "error": error}
    with prior_path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"{run_id}: replay-identical={identical}", flush=True)
    if not identical:
        raise RuntimeError(f"Replay diverged: {run_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_ids", nargs="*")
    parser.add_argument("--all-failures", action="store_true")
    args = parser.parse_args()
    entries = runs()
    chosen = args.run_ids
    if args.all_failures:
        chosen += [run_id for run_id, record in entries.items() if record["outcome"] == "fail" and run_id not in chosen]
    if not chosen:
        parser.error("Provide run IDs or --all-failures")
    for run_id in chosen:
        if run_id not in entries:
            parser.error(f"Unknown run ID: {run_id}")
        replay(entries[run_id])


if __name__ == "__main__":
    main()
