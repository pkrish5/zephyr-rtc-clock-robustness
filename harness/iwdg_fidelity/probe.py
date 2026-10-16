#!/usr/bin/env python3
"""Frozen STM32 IWDG reset/reboot/retained-state feasibility probe."""

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
SOURCE = UPSTREAM / "tests/drivers/watchdog/wdt_basic_api"
VARIANT = os.environ.get("IWDG_FIDELITY_VARIANT", "original")
if VARIANT not in ("original", "configured"):
    raise ValueError("IWDG_FIDELITY_VARIANT must be original or configured")
RESULTS = ROOT / ("results/iwdg_fidelity" if VARIANT == "original" else
                  "results/iwdg_fidelity_configured")
ELF = ROOT / ("subjects/iwdg_fidelity/build/zephyr/zephyr.elf" if VARIANT == "original" else
              "subjects/iwdg_fidelity/build_configured/zephyr/zephyr.elf")
RENODE = Path(os.environ.get("RENODE_BIN", "/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode"))
WEST = ROOT / ".venv/bin/west"
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
CASE_ID = "wdt_basic_test_suite.test_wdt"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    record = RESULTS / "build.json"
    if record.exists():
        saved = json.loads(record.read_text())
        if sha(ELF) != saved["elf_sha256"]:
            raise ValueError("Frozen IWDG ELF changed")
        print("IWDG existing build audited")
        return
    commit = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if commit != "3568e1b6d5cdd51a6b964a2a1d6d29200fea2056":
        raise ValueError("Unexpected Zephyr commit")
    overlays = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay",
                SOURCE / "boards/stm32_iwdg.overlay"]
    files = [SOURCE / "src/main.c", SOURCE / "src/test_wdt.c", SOURCE / "prj.conf",
             SOURCE / "CMakeLists.txt", ROOT / "notes/IWDG_FIDELITY_PROTOCOL.md"] + overlays
    if VARIANT == "configured":
        files.extend((ROOT / "subjects/iwdg_fidelity/disable_at_boot.conf",
                      ROOT / "notes/IWDG_FIDELITY_AMENDMENT.md"))
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    cmd = [str(WEST), "build", "-p", "always", "-b", "stm32f4_disco", str(SOURCE),
           "-d", str(ELF.parent.parent), "--",
           "-DDTC_OVERLAY_FILE=" + ";".join(map(str, overlays))]
    if VARIANT == "configured":
        cmd.append("-DEXTRA_CONF_FILE=" + str(ROOT / "subjects/iwdg_fidelity/disable_at_boot.conf"))
    env = dict(os.environ)
    env["ZEPHYR_BASE"] = str(UPSTREAM)
    env["ZEPHYR_SDK_INSTALL_DIR"] = env.get("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/phase1-zephyr-sdk")
    env["PATH"] = f"{WEST.parent}:{env['PATH']}"
    log = RESULTS / "build.log"
    with log.open("x") as stream:
        proc = subprocess.run(cmd, cwd=UPSTREAM, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, check=False)
    data = {"variant": VARIANT, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "zephyr_commit": commit, "board": "stm32f4_disco/stm32f407xx",
            "command": cmd, "exit_code": proc.returncode, "input_sha256": hashes,
            "build_log_path": str(log.relative_to(ROOT)), "build_log_sha256": sha(log),
            "elf_path": str(ELF.relative_to(ROOT)) if ELF.exists() else None,
            "elf_sha256": sha(ELF) if ELF.exists() else None}
    record.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"IWDG build exit={proc.returncode}, elf={data['elf_sha256']}")


def run(condition: str, index: int) -> None:
    if condition == "nominal" and index not in range(3):
        raise ValueError("Nominal index must be 0..2")
    if condition != "nominal" and index != 0:
        raise ValueError("Endpoint index must be zero")
    hz = {"nominal": 32000, "min": 17000, "max": 47000}[condition]
    build_record_path = RESULTS / "build.json"
    frozen = json.loads(build_record_path.read_text())
    if frozen["exit_code"] != 0 or sha(ELF) != frozen["elf_sha256"]:
        raise ValueError("IWDG build missing or changed")
    for path_str, digest in frozen["input_sha256"].items():
        if sha(ROOT / path_str) != digest:
            raise ValueError(f"IWDG input changed: {path_str}")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if version != json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())["renode_version"]:
        raise ValueError("Renode version changed")
    base = (RENODE.parent / "platforms/cpus/stm32f4.repl").read_text()
    systick, clock = "systickFrequency: 72000000", "frequency: 32000"
    marker = "iwdg: Timers.STM32_IndependentWatchdog @ sysbus 0x40003000"
    if base.count(systick) != 1 or base.count(marker) != 1:
        raise ValueError("Renode STM32F4 platform changed")
    before, after = base.split(marker, 1)
    if after.count(clock) < 1 or not after.lstrip().startswith(clock):
        raise ValueError("IWDG frequency field changed")
    configured = (before + marker + after.replace(clock, f"frequency: {hz}", 1)).replace(
        systick, "systickFrequency: 16000000")
    platform = RESULTS / "platforms" / f"stm32f4_iwdg_{hz}.repl"
    platform.parent.mkdir(parents=True, exist_ok=True)
    if platform.exists():
        if platform.read_text() != configured:
            raise ValueError("Saved IWDG platform changed")
    else:
        platform.write_text(configured)
    run_id = f"iwdg-{condition}-{index:03d}"
    record = RESULTS / "records" / f"{run_id}.json"
    uart = RESULTS / "uart" / f"{run_id}.log"
    monitor = RESULTS / "monitor" / f"{run_id}.log"
    trace_path = RESULTS / "traces" / f"{run_id}.json"
    for path in (record, uart, monitor, trace_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if record.exists():
        print(f"{run_id}: already recorded")
        return
    if any(path.exists() for path in (uart, monitor, trace_path)):
        raise RuntimeError(f"Unrecorded IWDG artifact exists: {run_id}")
    observations = []
    outcome, error, virtual_ns = "timeout", None, 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ELF, monitor) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
            for _ in range(120):
                session.run_for_ns(250_000_000)
                virtual_ns += 250_000_000
                output = uart.read_text(errors="replace") if uart.exists() else ""
                selected = [s.lower() for s, c in CASE.findall(output) if c == CASE_ID]
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "wait_for_reset_count": output.count("Waiting to restart MCU"),
                                     "testcase_passed_count": output.count("Testcase passed"),
                                     "suite_start_count": output.count("Running TESTSUITE"),
                                     "selected_case": selected[-1] if selected else None})
                if selected:
                    outcome = selected[-1]
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    output = uart.read_text(errors="replace") if uart.exists() else ""
    trace = {"run_id": run_id, "outcome": outcome, "error": error,
             "observations": observations,
             "cases": [{"status": s.lower(), "case": c} for s, c in CASE.findall(output)]}
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    waits = [x["virtual_ns"] for x in observations if x["wait_for_reset_count"] > 0]
    passes = [x["virtual_ns"] for x in observations if x["testcase_passed_count"] > 0]
    record_data = {"variant": VARIANT, "run_id": run_id,
                   "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                   "condition": condition, "index": index, "lsi_frequency_hz": hz,
                   "lsi_bound_hz": [17000, 47000], "cpu_performance_mips": 16,
                   "systick_frequency_hz": 16000000, "quantum_ns": 1000,
                   "step_ns": 250000000, "max_virtual_sec": 30,
                   "zephyr_commit": frozen["zephyr_commit"],
                   "build_record_sha256": sha(build_record_path),
                   "elf_sha256": frozen["elf_sha256"], "renode_version": version,
                   "platform_path": str(platform.relative_to(ROOT)), "platform_sha256": sha(platform),
                   "outcome": outcome, "error": error, "virtual_ns": virtual_ns,
                   "first_wait_virtual_ns": waits[0] if waits else None,
                   "first_testcase_pass_virtual_ns": passes[0] if passes else None,
                   "suite_start_count": output.count("Running TESTSUITE"),
                   "testcase_passed_count": output.count("Testcase passed"),
                   "wall_seconds": round(time.monotonic() - started, 3),
                   "uart_path": str(uart.relative_to(ROOT)), "uart_sha256": sha(uart) if uart.exists() else None,
                   "monitor_path": str(monitor.relative_to(ROOT)), "monitor_sha256": sha(monitor) if monitor.exists() else None,
                   "trace_path": str(trace_path.relative_to(ROOT)), "trace_sha256": sha(trace_path)}
    record.write_text(json.dumps(record_data, indent=2, sort_keys=True) + "\n")
    print(f"{run_id}: {outcome}, boot starts={record_data['suite_start_count']}, "
          f"testcase passed={record_data['testcase_passed_count']}, virtual={virtual_ns/1e9:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("build", "run"), required=True)
    parser.add_argument("--condition", choices=("nominal", "min", "max"), default="nominal")
    parser.add_argument("--index", type=int, default=0)
    args = parser.parse_args()
    if args.stage == "build":
        build()
    else:
        run(args.condition, args.index)


if __name__ == "__main__":
    main()
