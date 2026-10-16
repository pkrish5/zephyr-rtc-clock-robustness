#!/usr/bin/env python3
"""Build and nominal-screen the two selected, unchanged upstream RTC cases."""

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

UPSTREAM = ROOT / "subjects/upstream/zephyr"
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
WEST = ROOT / ".venv/bin/west"
CASES = {
    "counting": ("rtc_counting", "test_time_incrementing.c", "rtc_api.test_time_counting", 60),
    "alarm_pending": ("rtc_alarm_pending", "test_alarm.c", "rtc_api.test_alarm", 90),
}
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def paths(subject: str) -> tuple[dict, Path, Path, Path, Path]:
    directory, source, case, cap = CASES[subject]
    config = ROOT / "subjects" / directory
    results = ROOT / "results" / directory
    wrapper = config / "selected_case"
    elf = config / "build/selected_case/zephyr/zephyr.elf"
    return {"id": subject, "directory": directory, "source": source,
            "case": case, "cap": cap}, config, results, wrapper, elf


def build(subject: str) -> None:
    spec, config, results, wrapper, elf = paths(subject)
    results.mkdir(parents=True, exist_ok=True)
    record_path = results / "build.json"
    if record_path.exists():
        saved = json.loads(record_path.read_text())
        if sha(ROOT / saved["elf_path"]) != saved["elf_sha256"]:
            raise ValueError("Frozen selected-case ELF changed")
        print(f"{subject}: existing build audited", flush=True)
        return
    expected_commit = "3568e1b6d5cdd51a6b964a2a1d6d29200fea2056"
    actual = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected_commit:
        raise ValueError("Upstream Zephyr commit changed")
    log = results / "build.log"
    if log.exists():
        raise RuntimeError("Unrecorded build log exists")
    overlays = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay",
                ROOT / "subjects/phase1_lsi_rtc/rtc_alias.overlay"]
    source_dir = UPSTREAM / "tests/drivers/rtc/rtc_api/src"
    source_files = [source_dir / "main.c", source_dir / spec["source"]]
    input_files = source_files + [wrapper / "CMakeLists.txt", wrapper / "prj.conf",
                                  config / "PROTOCOL.md"] + overlays
    input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in input_files}
    cmd = [str(WEST), "build", "-p", "always", "-b", "stm32f4_disco", str(wrapper),
           "-d", str(elf.parent.parent), "--",
           "-DDTC_OVERLAY_FILE=" + ";".join(map(str, overlays))]
    env = dict(os.environ)
    env["ZEPHYR_BASE"] = str(UPSTREAM)
    env["ZEPHYR_SDK_INSTALL_DIR"] = env.get("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/phase1-zephyr-sdk")
    env["PATH"] = f"{WEST.parent}:{env['PATH']}"
    with log.open("x") as stream:
        proc = subprocess.run(cmd, cwd=UPSTREAM, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, check=False)
    record = {"subject": subject, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "zephyr_commit": actual, "board": "stm32f4_disco/stm32f407xx",
              "case": spec["case"], "command": cmd, "exit_code": proc.returncode,
              "input_sha256": input_hashes, "build_log_path": str(log.relative_to(ROOT)),
              "build_log_sha256": sha(log),
              "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
              "elf_sha256": sha(elf) if elf.exists() else None}
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"{subject}: build exit={proc.returncode}, elf={record['elf_sha256']}", flush=True)


def nominal(subject: str, index: int, series: int) -> None:
    if index not in range(5):
        raise ValueError("Nominal index must be 0..4")
    if series not in (1, 2):
        raise ValueError("Nominal series must be 1 or 2")
    spec, config, results, _, elf = paths(subject)
    record_path = results / "build.json"
    build_record = json.loads(record_path.read_text())
    if build_record["exit_code"] != 0 or sha(elf) != build_record["elf_sha256"]:
        raise ValueError("Selected-case build missing or changed")
    for path_str, digest in build_record["input_sha256"].items():
        if sha(ROOT / path_str) != digest:
            raise ValueError(f"Frozen build input changed: {path_str}")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    plan_version = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())["renode_version"]
    if version != plan_version:
        raise ValueError("Renode version changed")
    base = (RENODE.parent / "platforms/cpus/stm32f4.repl").read_text()
    systick = "systickFrequency: 72000000"
    rtc = "rtc: Timers.STM32F4_RTC @ sysbus 0x40002800"
    if base.count(systick) != 1 or base.count(rtc) != 1:
        raise ValueError("Renode platform layout changed")
    configured = base.replace(systick, "systickFrequency: 16000000").replace(
        rtc, rtc + "\n    wakeupTimerFrequency: 32000")
    platform = results / "platforms/stm32f4_rtc_lsi_32000.repl"
    platform.parent.mkdir(parents=True, exist_ok=True)
    if platform.exists():
        if platform.read_text() != configured:
            raise ValueError("Saved nominal platform changed")
    else:
        platform.write_text(configured)
    run_id = (f"{subject}-nominal-{index:03d}" if series == 1 else
              f"{subject}-nominal-s{series}-{index:03d}")
    raw = results / "nominal_records" / f"{run_id}.json"
    uart = results / "uart" / f"{run_id}.log"
    monitor = results / "monitor" / f"{run_id}.log"
    trace_path = results / "traces" / f"{run_id}.json"
    for path in (raw, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        print(f"{run_id}: already recorded", flush=True)
        return
    if any(p.exists() for p in (uart, monitor, trace_path)):
        raise RuntimeError(f"Unrecorded nominal artifact exists: {run_id}")
    observations = []
    outcome, error, virtual_ns = "timeout", None, 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, elf, monitor) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(spec["cap"] * 2):
                session.run_for_ns(500_000_000)
                virtual_ns += 500_000_000
                output = uart.read_text(errors="replace") if uart.exists() else ""
                selected = [status.lower() for status, case in CASE.findall(output)
                            if case == spec["case"]]
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "selected_case": selected[-1] if selected else None,
                                     "completed": any(marker in output for marker in MARKERS)})
                if any(marker in output for marker in MARKERS):
                    if len(selected) != 1:
                        outcome, error = "unknown", f"Expected one selected verdict: {selected}"
                    else:
                        outcome = selected[0]
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    trace = {"run_id": run_id, "subject": subject, "outcome": outcome, "error": error,
             "observations": observations,
             "cases": [{"status": s.lower(), "case": c} for s, c in CASE.findall(output)]}
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    record = {"run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "nominal_series": series,
              "subject": subject, "condition": "nominal", "case": spec["case"],
              "seed": None, "lsi_frequency_hz": 32000, "lsi_bound_hz": [17000, 47000],
              "cpu_performance_mips": 16, "systick_frequency_hz": 16000000,
              "quantum_ns": 1000, "step_ns": 500000000, "max_virtual_sec": spec["cap"],
              "zephyr_commit": build_record["zephyr_commit"],
              "source_and_config_sha256": build_record["input_sha256"],
              "build_record_sha256": sha(record_path),
              "elf_sha256": build_record["elf_sha256"], "renode_version": version,
              "platform_path": str(platform.relative_to(ROOT)), "platform_sha256": sha(platform),
              "outcome": outcome, "error": error, "virtual_ns": virtual_ns,
              "wall_seconds": round(time.monotonic() - started, 3),
              "uart_path": str(uart.relative_to(ROOT)), "uart_sha256": sha(uart) if uart.exists() else None,
              "monitor_path": str(monitor.relative_to(ROOT)), "monitor_sha256": sha(monitor) if monitor.exists() else None,
              "trace_path": str(trace_path.relative_to(ROOT)), "trace_sha256": sha(trace_path)}
    raw.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"{run_id}: {outcome}, virtual={virtual_ns/1e9:.1f}s, wall={record['wall_seconds']:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", choices=CASES, required=True)
    parser.add_argument("--stage", choices=("build", "nominal"), required=True)
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--series", type=int, default=1)
    args = parser.parse_args()
    if args.stage == "build":
        build(args.subject)
    else:
        nominal(args.subject, args.index, args.series)


if __name__ == "__main__":
    main()
