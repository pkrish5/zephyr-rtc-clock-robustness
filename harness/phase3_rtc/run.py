#!/usr/bin/env python3
"""Frozen RTC test versions under registered, seeded LSI schedules."""

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
sys.path.insert(0, str(ROOT / "harness/phase0"))
from session import RenodeSession  # noqa: E402

RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
PLAN = ROOT / "subjects/phase3_rtc/plan.json"
RESULTS = ROOT / "results/phase3_rtc"
MIN_HZ, NOMINAL_HZ, MAX_HZ = 17_000, 32_000, 47_000
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")
VERSIONS = {
    "upstream": {
        "source": "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c",
        "elf": "subjects/phase1_lsi_rtc/build/rtc_alarm_callback/zephyr/zephyr.elf",
        "case": "rtc_api.test_alarm_callback",
        "cohort": "upstream_selected",
    },
    "luna_primary_r04": {
        "source": "generated/phase2_luna/suites/rtc_alarm_callback/r04/test.c",
        "elf": "generated/phase2_luna/build/rtc_alarm_callback/r04/zephyr/zephyr.elf",
        "case": "rtc_alarm.test_both_alarm_channels",
        "cohort": "luna_primary",
    },
    "rtc_bound_r05": {
        "source": "generated/phase2_rtc_bound/suites/rtc_alarm_callback/r05/test.c",
        "elf": "generated/phase2_rtc_bound/build/rtc_alarm_callback/r05/zephyr/zephyr.elf",
        "case": "rtc_alarm.test_both_alarm_channels",
        "cohort": "rtc_bound_supplement",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_for(hz: int) -> Path:
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


def init_plan() -> None:
    if PLAN.exists():
        raise RuntimeError(f"Plan already exists: {PLAN}")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT / "subjects/upstream/zephyr"), "rev-parse", "HEAD"],
        text=True).strip()
    if commit != "3568e1b6d5cdd51a6b964a2a1d6d29200fea2056":
        raise RuntimeError(f"Unexpected Zephyr commit: {commit}")
    records = {}
    for ident, paths in VERSIONS.items():
        records[ident] = {**paths,
                          "source_sha256": sha256(ROOT / paths["source"]),
                          "elf_sha256": sha256(ROOT / paths["elf"]),
                          "phase2_oracle_adequate": False if ident != "upstream" else None}
    schedule = [random.Random(seed).randint(MIN_HZ, MAX_HZ) for seed in range(100)]
    plan = {
        "schema_version": 1,
        "protocol": "subjects/phase3_rtc/PROTOCOL.md",
        "protocol_sha256": sha256(ROOT / "subjects/phase3_rtc/PROTOCOL.md"),
        "registered_utc": datetime.now(timezone.utc).isoformat(),
        "zephyr_commit": commit,
        "renode_version": version,
        "board": "stm32f4_disco/stm32f407xx",
        "cpu_performance_mips": 16,
        "systick_frequency_hz": 16_000_000,
        "quantum_ns": 1000,
        "step_ns": 500_000_000,
        "max_virtual_sec": 60,
        "lsi_bound_hz": [MIN_HZ, MAX_HZ],
        "lsi_bound_source": "STM32F407 DS8626 Rev 12 Table 35; VDD 3 V; TA -40 to 105 C",
        "nominal_repeats": 5,
        "seed_start": 0,
        "seed_count": 100,
        "seed_distribution": "random.Random(seed).randint(17000, 47000)",
        "seeded_frequencies_hz": schedule,
        "endpoints_hz": {"min": MIN_HZ, "max": MAX_HZ},
        "versions": records,
    }
    PLAN.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"registered {len(records)} versions and {len(schedule)} seeded schedules; "
          f"distinct frequencies={len(set(schedule))}; plan_sha256={sha256(PLAN)}")


def validate_plan() -> dict:
    plan = json.loads(PLAN.read_text())
    if plan["protocol_sha256"] != sha256(ROOT / plan["protocol"]):
        raise RuntimeError("Registered protocol changed")
    if plan["zephyr_commit"] != subprocess.check_output(
            ["git", "-C", str(ROOT / "subjects/upstream/zephyr"), "rev-parse", "HEAD"],
            text=True).strip():
        raise RuntimeError("Zephyr commit changed")
    for ident, version in plan["versions"].items():
        if sha256(ROOT / version["source"]) != version["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {ident}")
        if sha256(ROOT / version["elf"]) != version["elf_sha256"]:
            raise RuntimeError(f"Frozen ELF changed: {ident}")
    expected = [random.Random(seed).randint(MIN_HZ, MAX_HZ) for seed in range(100)]
    if plan["seeded_frequencies_hz"] != expected:
        raise RuntimeError("Registered schedule list changed")
    return plan


def run_one(plan: dict, ident: str, condition: str, index: int) -> None:
    version = plan["versions"][ident]
    if condition == "nominal":
        if index not in range(plan["nominal_repeats"]):
            raise ValueError("Nominal repeat out of range")
        hz = NOMINAL_HZ
        run_id = f"{ident}-nominal-{index:03d}"
    elif condition == "seeded":
        if index not in range(plan["seed_count"]):
            raise ValueError("Seed out of range")
        hz = plan["seeded_frequencies_hz"][index]
        run_id = f"{ident}-seeded-{index:03d}"
    else:
        if condition not in ("min", "max") or index != 0:
            raise ValueError("Endpoint condition or index invalid")
        hz = plan["endpoints_hz"][condition]
        run_id = f"{ident}-{condition}"
    if condition != "nominal":
        nominal = [RESULTS / "records" / f"{ident}-nominal-{i:03d}.json"
                   for i in range(plan["nominal_repeats"])]
        if not all(path.exists() and json.loads(path.read_text())["outcome"] == "pass"
                   for path in nominal):
            raise RuntimeError(f"{ident} has not passed all registered nominal repeats")
    platform = path_for(hz)
    record_path = RESULTS / "records" / f"{run_id}.json"
    uart = RESULTS / "uart" / f"{run_id}.log"
    monitor = RESULTS / "monitor" / f"{run_id}.log"
    trace_path = RESULTS / "traces" / f"{run_id}.json"
    for path in (record_path, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if record_path.exists():
        print(f"{run_id}: already recorded", flush=True)
        return
    if any(path.exists() for path in (uart, monitor, trace_path)):
        raise RuntimeError(f"Refusing to overwrite unrecorded artifact: {run_id}")
    if sha256(ROOT / version["elf"]) != version["elf_sha256"] or sha256(ROOT / version["source"]) != version["source_sha256"]:
        raise RuntimeError("Frozen artifact changed")
    if subprocess.check_output([str(RENODE), "--version"], text=True).strip() != plan["renode_version"]:
        raise RuntimeError("Renode version changed")
    observations = []
    outcome, error = "timeout", None
    virtual_ns = 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ROOT / version["elf"], monitor) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(plan["max_virtual_sec"] * 1_000_000_000 // plan["step_ns"]):
                session.run_for_ns(plan["step_ns"])
                virtual_ns += plan["step_ns"]
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
                        error = f"Expected exactly one selected case verdict, found {selected}"
                    else:
                        outcome = selected[0]
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    cases = [{"status": status.lower(), "case": case} for status, case in CASE.findall(output)]
    trace = {"run_id": run_id, "condition": condition, "index": index,
             "lsi_frequency_hz": hz, "observations": observations,
             "cases": cases, "outcome": outcome, "error": error}
    trace_path.write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n")
    record = {
        "run_id": run_id, "version_id": ident, "cohort": version["cohort"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "condition": condition, "index": index,
        "seed": index if condition == "seeded" else None,
        "lsi_frequency_hz": hz,
        "lsi_bound_hz": plan["lsi_bound_hz"],
        "lsi_bound_source": plan["lsi_bound_source"],
        "cpu_performance_mips": plan["cpu_performance_mips"],
        "systick_frequency_hz": plan["systick_frequency_hz"],
        "quantum_ns": plan["quantum_ns"], "step_ns": plan["step_ns"],
        "max_virtual_sec": plan["max_virtual_sec"],
        "zephyr_commit": plan["zephyr_commit"],
        "plan_sha256": sha256(PLAN),
        "renode_version": plan["renode_version"],
        "source_path": version["source"], "source_sha256": version["source_sha256"],
        "elf_path": version["elf"], "elf_sha256": version["elf_sha256"],
        "platform_path": str(platform.relative_to(ROOT)),
        "platform_sha256": sha256(platform),
        "outcome": outcome, "error": error, "cases": cases,
        "virtual_ns": virtual_ns,
        "wall_seconds": round(time.monotonic() - started, 3),
        "uart_path": str(uart.relative_to(ROOT)),
        "uart_sha256": sha256(uart) if uart.exists() else None,
        "monitor_path": str(monitor.relative_to(ROOT)),
        "monitor_sha256": sha256(monitor) if monitor.exists() else None,
        "trace_path": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha256(trace_path),
    }
    record_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(f"{run_id}: {outcome}, LSI={hz}, virtual={virtual_ns/1e9:.1f}s, wall={record['wall_seconds']:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-plan", action="store_true")
    parser.add_argument("--version", choices=VERSIONS)
    parser.add_argument("--condition", choices=("nominal", "seeded", "min", "max"))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    if args.init_plan:
        init_plan()
        return
    if not args.version or not args.condition or args.start < 0 or args.count < 1:
        parser.error("version, condition, nonnegative start, and positive count are required")
    if args.condition in ("min", "max") and (args.start != 0 or args.count != 1):
        parser.error("Endpoint conditions have one run")
    plan = validate_plan()
    for index in range(args.start, args.start + args.count):
        run_one(plan, args.version, args.condition, index)


if __name__ == "__main__":
    main()
