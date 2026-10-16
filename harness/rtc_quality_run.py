#!/usr/bin/env python3
"""One fresh-process nominal-clock Renode quality challenge, immutable outputs."""

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness/phase3_rtc"))
from run import CASE, MARKERS, RENODE, RenodeSession  # noqa: E402

PLATFORM = ROOT / "results/phase3_rtc/platforms/stm32f4_rtc_lsi_32000.repl"
DELAY = re.compile(r"QUALITY_DELAY path=(\w+) request_us=(\d+) cycles=(\d+) hz=(\d+)")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def simulate(out, run_id, suite_id, family, kind, selected_case, source_sha,
             elf, manifest, max_virtual_sec=70, delay_us=None):
    registered = json.loads(manifest.read_text())
    renode_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if renode_version != registered["renode_version"]:
        raise RuntimeError("Renode version differs from registered version")
    paths = {kind: out / folder / f"{run_id}.{ext}" for kind, folder, ext in
             (("record", "records", "json"), ("trace", "traces", "json"),
              ("uart", "uart", "log"), ("monitor", "monitor", "log"))}
    if paths["record"].exists():
        return json.loads(paths["record"].read_text())
    if any(paths[k].exists() for k in ("trace", "uart", "monitor")):
        raise RuntimeError(f"Incomplete prior challenge: {run_id}")
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    observations, outcome, error, virtual_ns = [], "timeout", None, 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, PLATFORM, elf, paths["monitor"]) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{paths['uart']} true")
            for _ in range(2 * max_virtual_sec):
                session.run_for_ns(500000000)
                virtual_ns += 500000000
                output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
                cases = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": cases[-1] if cases else None})
                if any(marker in output for marker in MARKERS):
                    if selected_case:
                        statuses = [status for status, case in cases if case == selected_case]
                        outcome = statuses[0].lower() if len(statuses) == 1 else "unknown"
                        if outcome == "unknown":
                            error = f"Selected case verdicts: {statuses}"
                    elif any(status == "FAIL" for status, _ in cases):
                        outcome = "fail"
                    elif cases and all(status == "PASS" for status, _ in cases):
                        outcome = "pass"
                    else:
                        outcome, error = "unknown", "No unambiguous ztest verdict"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
    cases = [{"status": status.lower(), "case": case} for status, case in CASE.findall(output)]
    delays = [{"path": path, "requested_us": int(requested), "cycles": int(cycles),
               "clock_hz": int(hz), "achieved_us": int(cycles) * 1000000 / int(hz)}
              for path, requested, cycles, hz in DELAY.findall(output)]
    trace = {"run_id": run_id, "observations": observations, "cases": cases,
             "delay_measurements": delays, "outcome": outcome, "error": error}
    write_new(paths["trace"], trace)
    record = {"run_id": run_id, "suite_id": suite_id, "family": family, "kind": kind,
              "selected_case": selected_case, "delay_us": delay_us,
              "outcome": outcome, "error": error, "cases": cases,
              "delay_measurements": delays, "virtual_ns": virtual_ns,
              "wall_seconds": round(time.monotonic() - started, 3),
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": sha(manifest), "source_sha256": source_sha,
              "elf_sha256": sha(elf), "platform_path": str(PLATFORM.relative_to(ROOT)),
              "platform_sha256": sha(PLATFORM),
              "renode_version": renode_version, "cpu_performance_mips": 16,
              **{f"{k}_path": str(paths[k].relative_to(ROOT)) for k in
                 ("trace", "uart", "monitor")},
              **{f"{k}_sha256": sha(paths[k]) if paths[k].exists() else None for k in
                 ("trace", "uart", "monitor")}}
    write_new(paths["record"], record)
    print(f"{run_id}: {outcome}, virtual={virtual_ns/1e9:.1f}s, "
          f"wall={record['wall_seconds']:.1f}s", flush=True)
    return record
