#!/usr/bin/env python3
"""Execute the registered HSI 100-MIPS arm without changing its locked inputs."""

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
sys.path.insert(0, str(ROOT / "analysis"))
from session import RenodeSession  # noqa: E402
from phase3_hsi_plan import candidate  # noqa: E402

PLAN_PATH = ROOT / "subjects/phase3_hsi_100mips/plan.json"
# The first launch in the arm was an infrastructure failure before virtual time
# advanced: sandboxed Renode could not write its monitor history. Preserve it
# in the parent directory; the approved-access qualification has fresh IDs.
RESULTS = ROOT / "results/phase3_hsi_100mips/qualified"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan() -> dict:
    frozen = json.loads(PLAN_PATH.read_text())
    if candidate() != frozen:
        raise RuntimeError("Frozen HSI plan or one of its registered inputs changed")
    actual_version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if actual_version != frozen["renode_version"]:
        raise RuntimeError(f"Renode version changed: {actual_version}")
    return frozen


def key_for(version_id: str) -> str:
    return version_id.replace("/", "--")


def platform_for(hz: int) -> Path:
    base = (RENODE.parent / "platforms/cpus/stm32f4.repl").read_text()
    needle = "systickFrequency: 72000000"
    if base.count(needle) != 1:
        raise RuntimeError("Pinned Renode platform layout changed")
    configured = base.replace(needle, f"systickFrequency: {hz}")
    path = RESULTS / "platforms" / f"stm32f4_hsi_{hz}.repl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != configured:
            raise RuntimeError(f"Saved platform changed: {path}")
    else:
        path.write_text(configured)
    return path


def schedule(plan: dict, condition: str, index: int) -> tuple[int, int]:
    if condition == "nominal" and 0 <= index < plan["nominal_repeats"]:
        return plan["nominal_frequency_hz"], plan["nominal_cpu_mips"]
    if condition == "seeded" and 0 <= index < plan["seed_count"]:
        return plan["seeded_frequencies_hz"][index], plan["seeded_cpu_mips"][index]
    if condition == "min" and index == 0:
        return plan["endpoint_frequencies_hz"][0], plan["endpoint_cpu_mips"][0]
    if condition == "max" and index == 0:
        return plan["endpoint_frequencies_hz"][1], plan["endpoint_cpu_mips"][1]
    raise ValueError(f"Unregistered condition/index: {condition}/{index}")


def record_path(version_id: str, condition: str, index: int, root: Path) -> Path:
    run_id = f"{key_for(version_id)}-{condition}-{index:03d}"
    return root / "records" / f"{run_id}.json"


def run_one(plan: dict, version_id: str, condition: str, index: int,
            root: Path = RESULTS, require_screen: bool = True) -> dict:
    if version_id not in plan["inventory"]:
        raise ValueError(f"Unregistered version: {version_id}")
    version = plan["inventory"][version_id]
    hz, mips = schedule(plan, condition, index)
    run_id = f"{key_for(version_id)}-{condition}-{index:03d}"
    output_path = record_path(version_id, condition, index, root)
    if output_path.exists():
        saved = json.loads(output_path.read_text())
        if saved["run_id"] != run_id or saved["plan_sha256"] != sha(PLAN_PATH):
            raise RuntimeError(f"Stale existing record: {output_path}")
        return saved
    if condition != "nominal" and require_screen:
        screens = [record_path(version_id, "nominal", i, RESULTS)
                   for i in range(plan["nominal_repeats"])]
        if not all(p.exists() and json.loads(p.read_text())["outcome"] == "pass"
                   for p in screens):
            raise RuntimeError(f"Nominal 5/5 screen not passed: {version_id}")
    if sha(ROOT / version["elf_path"]) != version["elf_sha256"]:
        raise RuntimeError(f"Frozen ELF changed: {version_id}")
    if version["kind"] == "agent":
        if sha(ROOT / version["source_path"]) != version["source_sha256"]:
            raise RuntimeError(f"Frozen test source changed: {version_id}")
    else:
        for relative, expected in version["selected_case_sources"].items():
            if sha(ROOT / relative) != expected:
                raise RuntimeError(f"Frozen upstream source changed: {relative}")
    platform = platform_for(hz)
    uart = root / "uart" / f"{run_id}.log"
    monitor = root / "monitor" / f"{run_id}.log"
    trace_path = root / "traces" / f"{run_id}.json"
    for path in (output_path, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if any(path.exists() for path in (uart, monitor, trace_path)):
        raise RuntimeError(f"Refusing to overwrite raw output: {run_id}")
    observations = []
    virtual_ns = 0
    outcome, error = "timeout", None
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ROOT / version["elf_path"], monitor) as session:
            session.command(f"cpu PerformanceInMips {mips}")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(plan["max_virtual_sec"] * 1_000_000_000 // plan["observation_step_ns"]):
                session.run_for_ns(plan["observation_step_ns"])
                virtual_ns += plan["observation_step_ns"]
                output = uart.read_text(errors="replace") if uart.exists() else ""
                found = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": found[-1] if found else None,
                                     "completed": any(marker in output for marker in MARKERS)})
                if any(marker in output for marker in MARKERS):
                    selected = [status.lower() for status, name in found if name == version["case"]]
                    if version["kind"] == "upstream":
                        if len(selected) == 1:
                            outcome = selected[0]
                        else:
                            outcome, error = "unknown", f"Selected-case verdicts: {selected}"
                    elif not found:
                        outcome, error = "unknown", "No generated-suite case verdict"
                    elif any(status == "FAIL" for status, _ in found):
                        outcome = "fail"
                    elif "PROJECT EXECUTION FAILED" in output:
                        outcome, error = "unknown", "Project failed without a failing case verdict"
                    elif all(status == "PASS" for status, _ in found):
                        outcome = "pass"
                    else:
                        outcome, error = "unknown", "Generated-suite case skipped"
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": name} for status, name in CASE.findall(output)]
    trace = {"run_id": run_id, "condition": condition, "index": index,
             "hsi_frequency_hz": hz, "cpu_performance_mips": mips,
             "observations": observations, "cases": cases,
             "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    record = {
        "run_id": run_id, "version_id": version_id, "task_id": version["task_id"],
        "kind": version["kind"], "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "condition": condition, "index": index,
        "seed": index if condition == "seeded" else None,
        "hsi_frequency_hz": hz, "hsi_bound_hz": plan["hsi_bound_hz"],
        "hsi_bound_source": plan["bound_source"],
        "cpu_performance_mips": mips, "nominal_cpu_mips": plan["nominal_cpu_mips"],
        "systick_frequency_hz": hz, "quantum_ns": plan["quantum_ns"],
        "observation_step_ns": plan["observation_step_ns"],
        "max_virtual_sec": plan["max_virtual_sec"],
        "plan_sha256": sha(PLAN_PATH), "renode_version": plan["renode_version"],
        "elf_path": version["elf_path"], "elf_sha256": version["elf_sha256"],
        "source_path": version.get("source_path"),
        "source_sha256": version.get("source_sha256"),
        "selected_case_sources": version.get("selected_case_sources"),
        "selected_case": version["case"],
        "original_oracle_adequate": version["original_oracle_adequate"],
        "functional": version["functional"],
        "timing_bound": version.get("timing_bound"),
        "platform_path": str(platform.relative_to(ROOT)),
        "platform_sha256": sha(platform),
        "outcome": outcome, "error": error, "cases": cases,
        "project_marker": next((m for m in MARKERS if m in output), None),
        "virtual_ns": virtual_ns,
        "wall_seconds": round(time.monotonic() - started, 3),
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "monitor_sha256": sha(monitor) if monitor.exists() else None,
        "trace_path": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha(trace_path),
    }
    output_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(f"{run_id}: {outcome}, HSI={hz}, CPU={mips} MIPS, "
          f"virtual={virtual_ns/1e9:.2f}s, wall={record['wall_seconds']:.1f}s", flush=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="One registered version ID; default is all")
    parser.add_argument("--screen-only", action="store_true")
    parser.add_argument("--condition", choices=("nominal", "seeded", "min", "max"))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    args = parser.parse_args()
    plan = load_plan()
    versions = [args.version] if args.version else list(plan["inventory"])
    for ident in versions:
        if ident not in plan["inventory"]:
            parser.error(f"Unregistered version: {ident}")
        if args.condition:
            count = args.count if args.count is not None else 1
            for index in range(args.start, args.start + count):
                run_one(plan, ident, args.condition, index)
            continue
        for index in range(plan["nominal_repeats"]):
            run_one(plan, ident, "nominal", index)
        nominal = [json.loads(record_path(ident, "nominal", i, RESULTS).read_text())
                   for i in range(plan["nominal_repeats"])]
        if not all(row["outcome"] == "pass" for row in nominal):
            print(f"{ident}: excluded after nominal screen {[r['outcome'] for r in nominal]}", flush=True)
            continue
        if args.screen_only:
            continue
        for index in range(plan["seed_count"]):
            run_one(plan, ident, "seeded", index)
        run_one(plan, ident, "min", 0)
        run_one(plan, ident, "max", 0)


if __name__ == "__main__":
    main()
