#!/usr/bin/env python3
"""Five fresh nominal screens for frozen Stage B callback suites."""

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

BASE = ROOT / "generated/stage_b_callback_v1"
RESULTS = ROOT / "results/stage_b_callback_v1"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
SUCCESS = "PROJECT EXECUTION SUCCESSFUL"
FAILURE = "PROJECT EXECUTION FAILED"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_record(run_id):
    candidates = [RESULTS / "build_retry_records" / f"{run_id}.retry03.json",
                  RESULTS / "build_retry_records" / f"{run_id}.json",
                  RESULTS / "build_records" / f"{run_id}.json"]
    path = next((p for p in candidates if p.exists()), candidates[-1])
    return json.loads(path.read_text()) if path.exists() else None


def run_one(call, repeat, access_retry=False):
    model = call["model"].removeprefix("gpt-6-")
    run_id = f"{model}-{call['condition']}-rtc_alarm_callback-r{call['sample_index']:02d}"
    build = build_record(run_id)
    if not build or build["status"] != "pass":
        return "not_built"
    source = ROOT / build["source_path"]
    elf = ROOT / build["elf_path"]
    if sha(source) != build["source_sha256"] or sha(elf) != build["elf_sha256"]:
        raise ValueError(f"Frozen build inputs changed: {run_id}")
    platform = ROOT / "results/phase3_rtc/platforms/stm32f4_rtc_lsi_32000.repl"
    frequency, mips, step_ns, max_sec = 32_000, 16, 500_000_000, 60
    if not platform.exists():
        raise FileNotFoundError(platform)
    nominal_id = f"{run_id}-{'access-retry-' if access_retry else 'nominal-'}{repeat:03d}"
    output_prefix = "nominal_access_retry" if access_retry else "nominal"
    record_path = RESULTS / f"{output_prefix}_records" / f"{nominal_id}.json"
    if record_path.exists():
        record = json.loads(record_path.read_text())
        if record["elf_sha256"] != build["elf_sha256"]:
            raise ValueError(f"Frozen nominal record mismatch: {nominal_id}")
        return record["outcome"]
    uart = RESULTS / f"{output_prefix}_uart" / f"{nominal_id}.log"
    monitor = RESULTS / f"{output_prefix}_monitor" / f"{nominal_id}.log"
    trace_path = RESULTS / f"{output_prefix}_traces" / f"{nominal_id}.json"
    for path in (record_path, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError(f"Unrecorded nominal artifact exists: {path}")
    renode_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    observations = []
    virtual_ns = 0
    outcome, error = "timeout", None
    start = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, elf, monitor) as session:
            session.command(f"cpu PerformanceInMips {mips}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(max_sec * 1_000_000_000 // step_ns):
                session.run_for_ns(step_ns)
                virtual_ns += step_ns
                output = uart.read_text(errors="replace") if uart.exists() else ""
                matches = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": matches[-1] if matches else None,
                                     "completed": SUCCESS in output or FAILURE in output})
                if SUCCESS in output or FAILURE in output:
                    if not matches:
                        outcome, error = "unknown", "No ztest case verdict"
                    elif any(status == "FAIL" for status, _ in matches):
                        outcome = "fail"
                    elif FAILURE in output:
                        outcome, error = "unknown", "Project failure without failing case"
                    elif all(status == "PASS" for status, _ in matches):
                        outcome = "pass"
                    else:
                        outcome, error = "unknown", "Skipped case in generated suite"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": name} for status, name in CASE.findall(output)]
    trace = {"run_id": nominal_id, "condition": output_prefix, "repeat": repeat,
             "frequency_hz": frequency, "cpu_mips": mips, "observations": observations,
             "cases": cases, "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    record = {
        "run_id": nominal_id, "suite_run_id": run_id, "call_index": call["call_index"],
        "condition": output_prefix, "repeat": repeat,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome, "error": error, "cases": cases,
        "virtual_ns": virtual_ns, "wall_seconds": round(time.monotonic()-start, 3),
        "source_path": build["source_path"], "source_sha256": build["source_sha256"],
        "elf_path": build["elf_path"], "elf_sha256": build["elf_sha256"],
        "platform_path": str(platform.relative_to(ROOT)), "platform_sha256": sha(platform),
        "renode_version": renode_version, "frequency_hz": frequency,
        "cpu_performance_mips": mips, "quantum_ns": 1000,
        "observation_step_ns": step_ns, "max_virtual_sec": max_sec,
        "uart_path": str(uart.relative_to(ROOT)), "uart_sha256": sha(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)), "monitor_sha256": sha(monitor) if monitor.exists() else None,
        "trace_path": str(trace_path.relative_to(ROOT)), "trace_sha256": sha(trace_path),
    }
    with record_path.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"{nominal_id}: {outcome}; virtual={virtual_ns/1e9:.2f}s; wall={record['wall_seconds']:.1f}s", flush=True)
    return outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--call-index", type=int)
    parser.add_argument("--max-suites", type=int)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--repeats", type=int, choices=(1, 5), default=5)
    parser.add_argument("--functional-only", action="store_true")
    parser.add_argument("--access-retry", action="store_true",
                        help="Separate five-run qualification after original zero-time Renode history permission errors")
    args = parser.parse_args()
    order = json.loads((BASE / "call_order.json").read_text())["calls"]
    review_path = ROOT / "analysis/stage_b_callback_source_review.json"
    review = json.loads(review_path.read_text())["decisions"] if args.functional_only else {}
    completed = 0
    for call in order:
        if call["call_index"] < args.start_index:
            continue
        if args.call_index and call["call_index"] != args.call_index:
            continue
        if args.max_suites is not None and completed >= args.max_suites:
            break
        model = call["model"].removeprefix("gpt-6-")
        run_id = f"{model}-{call['condition']}-rtc_alarm_callback-r{call['sample_index']:02d}"
        if args.functional_only and review.get(run_id, {}).get("functional") != "met":
            continue
        build = build_record(run_id)
        if not build or build["status"] != "pass":
            continue
        if args.functional_only and review[run_id]["source_sha256"] != build["source_sha256"]:
            raise ValueError(f"Reviewed source and built source differ: {run_id}")
        if args.access_retry:
            if args.repeats != 5:
                raise ValueError("Access retry requires five original nominal records")
            for repeat in range(5):
                prior = RESULTS / "nominal_records" / f"{run_id}-nominal-{repeat:03d}.json"
                if not prior.exists():
                    raise ValueError(f"Missing original nominal record: {prior}")
                rec = json.loads(prior.read_text())
                monitor = ROOT / rec["monitor_path"]
                if rec["outcome"] != "harness_error" or rec["virtual_ns"] != 0 or "history' is denied" not in monitor.read_text(errors="replace"):
                    raise ValueError(f"Original was not the registered zero-time history permission error: {prior}")
        for repeat in range(args.repeats):
            run_one(call, repeat, access_retry=args.access_retry)
        completed += 1
    print(f"Compiled suites screened this invocation: {completed}", flush=True)


if __name__ == "__main__":
    main()
