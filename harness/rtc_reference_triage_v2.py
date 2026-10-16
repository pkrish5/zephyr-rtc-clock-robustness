#!/usr/bin/env python3
"""Access-retry namespace for the approved reference-oracle triage.

The first nominal attempts crashed before virtual time because the sandbox
denied Renode monitor-history writes. This runner reuses the same frozen
reference ELFs and saves fresh attempts without rewriting those originals.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness/phase3_rtc"))
from run import MARKERS, RENODE, RenodeSession  # noqa: E402

OUT = ROOT / "results/rtc_reference_triage_access"
BUILD_OUT = ROOT / "results/rtc_reference_triage"
PLAN = ROOT / "subjects/phase3_rtc/plan.json"
FAMILIES = {"rtc_alarm_callback": "callback", "rtc_time_counting": "counting",
            "rtc_alarm_pending": "pending"}
CASE = re.compile(r"- (PASS|FAIL|SKIP) - \[([^]]+)\]")
OVERLAYS = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay",
            ROOT / "subjects/phase1_lsi_rtc/rtc_alias.overlay"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def build(family):
    name = FAMILIES[family]
    app = ROOT / "subjects/reference_rtc" / name
    sources = [app / "test.c", app / "prj.conf", app / "CMakeLists.txt",
               ROOT / "subjects/reference_rtc/reference_common.h", *OVERLAYS]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    build_dir = app / "build"
    elf = build_dir / "zephyr/zephyr.elf"
    record = BUILD_OUT / "build" / f"{name}.json"
    if record.exists():
        saved = json.loads(record.read_text())
        if saved["input_sha256"] != inputs:
            raise RuntimeError(f"Reference source changed after build: {family}")
        if saved["status"] == "pass" and sha(elf) != saved["elf_sha256"]:
            raise RuntimeError(f"Reference ELF changed: {family}")
        print(f"{family}: existing build {saved['status']}", flush=True)
        return
    log = BUILD_OUT / "build_logs" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["ZEPHYR_BASE"] = str(ROOT / "subjects/upstream/zephyr")
    env["ZEPHYR_SDK_INSTALL_DIR"] = "/private/tmp/zephyr-sdk-0.17.4"
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    cmd = [str(ROOT / ".venv/bin/west"), "build", "-p", "always", "-b", "stm32f4_disco",
           str(app), "-d", str(build_dir), "--",
           "-DDTC_OVERLAY_FILE=" + ";".join(map(str, OVERLAYS))]
    with log.open("x") as stream:
        result = subprocess.run(cmd, cwd=ROOT / "subjects/upstream/zephyr", env=env,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=600, check=False)
    status = "pass" if result.returncode == 0 and elf.exists() else "build_fail"
    save_new(record, {"family": family, "timestamp_utc": stamp(), "command": cmd,
                      "status": status, "returncode": result.returncode,
                      "input_sha256": inputs, "log_path": str(log.relative_to(ROOT)),
                      "log_sha256": sha(log),
                      "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
                      "elf_sha256": sha(elf) if elf.exists() else None})
    print(f"{family}: {status} ({log.relative_to(ROOT)})", flush=True)


def register():
    plan = json.loads(PLAN.read_text())
    manifest = OUT / "manifest.json"
    builds = {}
    for family, name in FAMILIES.items():
        p = BUILD_OUT / "build" / f"{name}.json"
        b = json.loads(p.read_text())
        if b["status"] != "pass":
            raise RuntimeError(f"Cannot register failed reference: {family}")
        for rel, digest in b["input_sha256"].items():
            if sha(ROOT / rel) != digest:
                raise RuntimeError(f"Reference input changed: {rel}")
        if sha(ROOT / b["elf_path"]) != b["elf_sha256"]:
            raise RuntimeError(f"Reference ELF changed: {family}")
        builds[family] = {"build_record": str(p.relative_to(ROOT)),
                          "build_record_sha256": sha(p), **b}
    fail_seeds = defaultdict(set)
    for path in (ROOT / "results/rtc_factorial_v2/records").glob("*.json"):
        r = json.loads(path.read_text())
        if r["condition"] == "seeded" and r["outcome"] == "fail":
            fail_seeds[r["family"]].add(r["seed"])
    expected = {"rtc_alarm_callback": 26, "rtc_time_counting": 17, "rtc_alarm_pending": 26}
    if {k: len(fail_seeds[k]) for k in FAMILIES} != expected:
        raise RuntimeError("Observed failing-seed union changed")
    version = subprocess.check_output([str(RENODE), "--version"], text=True).strip()
    if version != plan["renode_version"]:
        raise RuntimeError("Renode version differs from registered arm")
    save_new(manifest, {"registered_utc": stamp(), "schema_version": 1,
                        "plan_sha256": sha(PLAN), "renode_version": version,
                        "reference_builds": builds,
                        "selected_seed_union": {k: sorted(v) for k, v in fail_seeds.items()},
                        "endpoints": ["min", "max"], "nominal_hz": 32000,
                        "runner_sha256": sha(Path(__file__))})
    print(f"Registered {sum(len(v) for v in fail_seeds.values()) + 6} reference challenges; "
          f"manifest {sha(manifest)}", flush=True)


def run(family, condition, seed):
    m = json.loads((OUT / "manifest.json").read_text())
    plan = json.loads(PLAN.read_text())
    if sha(PLAN) != m["plan_sha256"] or sha(Path(__file__)) != m["runner_sha256"]:
        raise RuntimeError("Reference runner or plan changed after registration")
    b = m["reference_builds"][family]
    if sha(ROOT / b["elf_path"]) != b["elf_sha256"]:
        raise RuntimeError("Reference ELF changed")
    for rel, digest in b["input_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Reference source changed: {rel}")
    if condition == "seeded":
        if seed not in m["selected_seed_union"][family]:
            raise RuntimeError("Seed not in registered failure union")
        hz = plan["seeded_frequencies_hz"][seed]
        run_id = f"{FAMILIES[family]}-seeded-{seed:03d}"
    else:
        hz = m["nominal_hz"] if condition == "nominal" else plan["endpoints_hz"][condition]
        run_id = f"{FAMILIES[family]}-{condition}"
    paths = {kind: OUT / folder / f"{run_id}.{ext}" for kind, folder, ext in
             (("record", "records", "json"), ("trace", "traces", "json"),
              ("uart", "uart", "log"), ("monitor", "monitor", "log"))}
    if paths["record"].exists():
        print(f"{run_id}: existing {json.loads(paths['record'].read_text())['outcome']}")
        return
    if any(paths[k].exists() for k in ("trace", "uart", "monitor")):
        raise RuntimeError(f"Incomplete prior artifact: {run_id}")
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    platform = ROOT / "results/phase3_rtc/platforms" / f"stm32f4_rtc_lsi_{hz}.repl"
    if not platform.exists():
        raise RuntimeError(f"Registered platform missing: {hz}")
    observations, outcome, error, virtual_ns = [], "timeout", None, 0
    started = time.monotonic()
    try:
        with RenodeSession(RENODE, platform, ROOT / b["elf_path"], paths["monitor"]) as session:
            session.command("cpu PerformanceInMips 16")
            session.command(f"sysbus.usart2 CreateFileBackend @{paths['uart']} true")
            for _ in range(120):
                session.run_for_ns(500_000_000)
                virtual_ns += 500_000_000
                output = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
                cases = CASE.findall(output)
                observations.append({"virtual_ns": virtual_ns,
                                     "uart_bytes": len(output.encode(errors="replace")),
                                     "latest_case": cases[-1] if cases else None})
                if any(marker in output for marker in MARKERS):
                    outcome = ("fail" if any(s == "FAIL" for s, _ in cases) else
                               "pass" if cases and all(s == "PASS" for s, _ in cases) else "unknown")
                    break
    except Exception as exc:
        outcome, error = "harness_error", f"{type(exc).__name__}: {exc}"
    cases = [{"status": s.lower(), "case": c} for s, c in CASE.findall(
        paths["uart"].read_text(errors="replace") if paths["uart"].exists() else "")]
    trace = {"run_id": run_id, "lsi_frequency_hz": hz, "outcome": outcome,
             "error": error, "cases": cases, "observations": observations}
    save_new(paths["trace"], trace)
    save_new(paths["record"], {"run_id": run_id, "family": family, "condition": condition,
                               "seed": seed if condition == "seeded" else None,
                               "lsi_frequency_hz": hz, "outcome": outcome, "error": error,
                               "cases": cases, "virtual_ns": virtual_ns,
                               "wall_seconds": round(time.monotonic()-started, 3),
                               "timestamp_utc": stamp(), "manifest_sha256": sha(OUT / "manifest.json"),
                               "source_sha256": b["input_sha256"], "elf_sha256": b["elf_sha256"],
                               "renode_version": m["renode_version"],
                               "platform_path": str(platform.relative_to(ROOT)),
                               "platform_sha256": sha(platform),
                               **{f"{k}_path": str(paths[k].relative_to(ROOT)) for k in
                                  ("trace", "uart", "monitor")},
                               **{f"{k}_sha256": sha(paths[k]) if paths[k].exists() else None for k in
                                  ("trace", "uart", "monitor")}})
    print(f"{run_id}: {outcome}, LSI={hz}, virtual={virtual_ns/1e9:.1f}s, "
          f"wall={time.monotonic()-started:.1f}s", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--build", choices=FAMILIES)
    p.add_argument("--register", action="store_true")
    p.add_argument("--run", choices=FAMILIES)
    p.add_argument("--condition", choices=("nominal", "min", "max", "seeded"))
    p.add_argument("--seed", type=int)
    a = p.parse_args()
    if a.build:
        build(a.build)
    elif a.register:
        register()
    elif a.run and a.condition:
        run(a.run, a.condition, a.seed)
    else:
        p.error("Specify --build, --register, or --run with --condition")


if __name__ == "__main__":
    main()
