#!/usr/bin/env python3
"""Replay frozen RTC LSI runs in fresh Renode processes."""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone

from run import (CASE_LINE, ELF, MARKERS, RENODE, RESULTS, ROOT, RenodeSession,
                 freeze, sha256)


def all_runs() -> dict:
    return {entry["run_id"]: entry for entry in map(json.loads, (RESULTS / "runs.jsonl").read_text().splitlines())}


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
    build = freeze()
    if sha256(ELF) != original["elf_sha256"] or build["elf_sha256"] != original["elf_sha256"]:
        raise RuntimeError(f"Frozen ELF changed: {run_id}")
    platform = ROOT / original["renode_platform_path"]
    if sha256(platform) != original["renode_platform_sha256"]:
        raise RuntimeError(f"Platform changed: {run_id}")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if version != original["renode_version"]:
        raise RuntimeError(f"Renode version changed: {run_id}")
    step_ns = original["step_ns"]
    outcome = "timeout"
    observations = []
    error = None
    start = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ELF, monitor) as session:
            session.command(f"cpu PerformanceInMips {original['cpu_performance_mips']}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for step in range(1, original["max_virtual_sec"] * 1_000_000_000 // step_ns + 1):
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
    previous = json.loads((ROOT / original["trace_path"]).read_text())
    identical = outcome == previous["outcome"] and cases == previous["cases"] and observations == previous["observations"]
    record = {"run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "identical_trace_and_verdict": identical, "outcome": outcome,
              "original_trace_path": original["trace_path"],
              "uart_path": str(uart.relative_to(ROOT)), "monitor_path": str(monitor.relative_to(ROOT)),
              "wall_seconds": round(time.monotonic() - start, 3), "error": error}
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
    entries = all_runs()
    chosen = list(args.run_ids)
    if args.all_failures:
        chosen.extend(run_id for run_id, entry in entries.items() if entry["outcome"] == "fail" and run_id not in chosen)
    if not chosen:
        parser.error("Provide run IDs or --all-failures")
    for run_id in chosen:
        if run_id not in entries:
            parser.error(f"Unknown run ID: {run_id}")
        replay(entries[run_id])


if __name__ == "__main__":
    main()
