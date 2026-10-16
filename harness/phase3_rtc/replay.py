#!/usr/bin/env python3
"""Replay every observed Phase 3 RTC flip in a fresh Renode process."""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone

from run import CASE, MARKERS, RENODE, RESULTS, ROOT, RenodeSession, sha256, validate_plan


def replay(original: dict, plan: dict, diagnose_harness_error: bool = False) -> None:
    run_id = original["run_id"]
    output_path = RESULTS / "replay_records" / f"{run_id}.json"
    uart = RESULTS / "replay_uart" / f"{run_id}.log"
    monitor = RESULTS / "replay_monitor" / f"{run_id}.log"
    trace_path = RESULTS / "replay_traces" / f"{run_id}.json"
    for path in (output_path, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        print(f"{run_id}: already replayed", flush=True)
        return
    if any(path.exists() for path in (uart, monitor, trace_path)):
        raise RuntimeError(f"Refusing to overwrite unrecorded replay artifact: {run_id}")
    if original["condition"] not in ("seeded", "min", "max") or (original["outcome"] != "fail" and
            not (diagnose_harness_error and original["outcome"] == "harness_error")):
        raise RuntimeError(f"Not a registered flip or requested harness-error diagnosis: {run_id}")
    if original["plan_sha256"] != sha256(ROOT / "subjects/phase3_rtc/plan.json"):
        raise RuntimeError("Plan hash mismatch")
    platform = ROOT / original["platform_path"]
    if sha256(platform) != original["platform_sha256"]:
        raise RuntimeError("Platform hash mismatch")
    version = plan["versions"][original["version_id"]]
    if sha256(ROOT / version["elf"]) != original["elf_sha256"]:
        raise RuntimeError("Frozen ELF changed")
    if subprocess.check_output([str(RENODE), "--version"], text=True).strip() != original["renode_version"]:
        raise RuntimeError("Renode version changed")
    observations = []
    outcome, error = "timeout", None
    virtual_ns = 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ROOT / version["elf"], monitor) as session:
            session.command(f"cpu PerformanceInMips {original['cpu_performance_mips']}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(original["max_virtual_sec"] * 1_000_000_000 // original["step_ns"]):
                session.run_for_ns(original["step_ns"])
                virtual_ns += original["step_ns"]
                output = uart.read_text(errors="replace") if uart.exists() else ""
                matches = CASE.findall(output)
                selected = [status.lower() for status, case in matches if case == version["case"]]
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "selected_case": selected[-1] if selected else None,
                                     "completed": any(marker in output for marker in MARKERS)})
                if any(marker in output for marker in MARKERS):
                    if len(selected) != 1:
                        outcome = "unknown"
                        error = f"Expected one selected case verdict, got {selected}"
                    else:
                        outcome = selected[0]
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": case} for status, case in CASE.findall(output)]
    trace = {"run_id": run_id, "condition": original["condition"], "index": original["index"],
             "lsi_frequency_hz": original["lsi_frequency_hz"], "observations": observations,
             "cases": cases, "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    previous = json.loads((ROOT / original["trace_path"]).read_text())
    identical = (outcome == previous["outcome"] and cases == previous["cases"]
                 and observations == previous["observations"] and error == previous["error"])
    record = {
        "run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "original_trace_path": original["trace_path"],
        "original_trace_sha256": original["trace_sha256"],
        "original_outcome": original["outcome"],
        "identical_trace_and_verdict": identical,
        "outcome": outcome, "error": error,
        "wall_seconds": round(time.monotonic() - started, 3),
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha256(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "monitor_sha256": sha256(monitor) if monitor.exists() else None,
        "trace_path": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha256(trace_path),
    }
    output_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(f"{run_id}: replay-identical={identical}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_ids", nargs="*")
    parser.add_argument("--all-failures", action="store_true")
    parser.add_argument("--diagnose-harness-error", action="store_true")
    args = parser.parse_args()
    plan = validate_plan()
    records = {json.loads(p.read_text())["run_id"]: json.loads(p.read_text())
               for p in (RESULTS / "records").glob("*.json")}
    chosen = list(args.run_ids)
    if args.all_failures:
        chosen.extend(ident for ident, row in sorted(records.items())
                      if row["outcome"] == "fail" and row["condition"] in ("seeded", "min", "max")
                      and ident not in chosen)
    if not chosen:
        parser.error("Provide run IDs or --all-failures")
    for run_id in chosen:
        if run_id not in records:
            parser.error(f"Unknown run ID: {run_id}")
        replay(records[run_id], plan, diagnose_harness_error=args.diagnose_harness_error)


if __name__ == "__main__":
    main()
