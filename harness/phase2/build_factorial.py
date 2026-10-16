#!/usr/bin/env python3
"""Build each frozen factorial C source without rewriting it."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "generated/spec_context_factorial_v1"
RESULTS = ROOT / "results/spec_context_factorial_v1"
TASKS = {row["id"]: row for row in json.loads((ROOT / "subjects/phase2_tasks_v2.json").read_text())["tasks"]}
WEST = ROOT / ".venv/bin/west"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_or_check(path, content):
    if path.exists():
        if path.read_text() != content:
            raise ValueError(f"Build input changed: {path}")
    else:
        path.write_text(content)


def build_one(call):
    model = call["model"].removeprefix("gpt-6-")
    run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
    run_dir = BASE / "suites" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
    meta_path = run_dir / "metadata.json"
    if not meta_path.exists():
        return "not_generated"
    generation = json.loads(meta_path.read_text())
    if generation["status"] != "generated":
        return generation["status"]
    source = run_dir / "test.c"
    if sha(source) != generation["source_sha256"] or generation["call_index"] != call["call_index"]:
        raise ValueError(f"Frozen generation mismatch: {run_id}")
    record_path = RESULTS / "build_records" / f"{run_id}.json"
    retry_path = RESULTS / "build_retry_records" / f"{run_id}.json"
    if record_path.exists():
        record = json.loads(record_path.read_text())
        if record["source_sha256"] != generation["source_sha256"]:
            raise ValueError(f"Frozen build mismatch: {run_id}")
        if retry_path.exists():
            retry = json.loads(retry_path.read_text())
            if retry["source_sha256"] != generation["source_sha256"]:
                raise ValueError(f"Frozen retry mismatch: {run_id}")
            return retry["status"]
        old_log = ROOT / record["log_path"]
        if record["status"] != "fail" or "Could not find a package configuration file provided by \"Zephyr-sdk\"" not in old_log.read_text():
            return record["status"]
        # Preserve the failed infrastructure attempt and its log. Retry once
        # with the restored same-version SDK in a separately named record.
        record_path = retry_path
    task = TASKS[call["task_id"]]
    cmake = run_dir / "CMakeLists.txt"
    conf = run_dir / "prj.conf"
    write_or_check(cmake, "cmake_minimum_required(VERSION 3.20.0)\n"
                   "find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})\n"
                   f"project(generated_{task['id']})\n"
                   "target_sources(app PRIVATE test.c)\n")
    write_or_check(conf, task["build_conf"])
    overlays = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay"]
    if task["arm"] == "lsi_pilot":
        overlays.append(ROOT / "subjects/phase1_lsi_rtc/rtc_alias.overlay")
    build_dir = BASE / "build" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
    log = RESULTS / "build_logs" / (f"{run_id}.retry02.log" if record_path == retry_path else f"{run_id}.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        raise ValueError(f"Unrecorded build log: {log}")
    env = os.environ.copy()
    env.setdefault("ZEPHYR_BASE", str(ROOT / "subjects/upstream/zephyr"))
    env.setdefault("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/zephyr-sdk-0.17.4")
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    cmd = [str(WEST), "build", "-p", "always", "-b", "stm32f4_disco",
           str(run_dir), "-d", str(build_dir), "--",
           "-DDTC_OVERLAY_FILE=" + ";".join(str(p) for p in overlays)]
    started = time.monotonic()
    try:
        with log.open("w") as stream:
            process = subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT,
                                     env=env, timeout=600, check=False)
        returncode, timed_out = process.returncode, False
    except subprocess.TimeoutExpired:
        returncode, timed_out = None, True
    elf = build_dir / "zephyr/zephyr.elf"
    status = "pass" if returncode == 0 and elf.exists() else "timeout" if timed_out else "fail"
    record = {
        "run_id": run_id, "call_index": call["call_index"], "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status, "returncode": returncode, "wall_seconds": round(time.monotonic()-started, 3),
        "model": call["model"], "condition": call["condition"], "task_id": call["task_id"],
        "source_path": str(source.relative_to(ROOT)), "source_sha256": sha(source),
        "metadata_sha256": sha(meta_path), "prompt_sha256": generation["prompt_sha256"],
        "cmake_sha256": sha(cmake), "prj_conf_sha256": sha(conf),
        "overlay_sha256": {str(p.relative_to(ROOT)): sha(p) for p in overlays},
        "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
        "elf_sha256": sha(elf) if elf.exists() else None,
        "log_path": str(log.relative_to(ROOT)), "log_sha256": sha(log),
        "zephyr_commit": json.loads((ROOT / "subjects/phase2_tasks_v2.json").read_text())["zephyr_commit"],
        "sdk_install_dir": env["ZEPHYR_SDK_INSTALL_DIR"],
        "retry_of": str((RESULTS / "build_records" / f"{run_id}.json").relative_to(ROOT)) if record_path == retry_path else None,
    }
    with record_path.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"{call['call_index']:03d}/390 {run_id}: build {status}", flush=True)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new", type=int, default=390)
    parser.add_argument("--follow", action="store_true", help="Continue building newly frozen outputs until all 390 calls finalize")
    args = parser.parse_args()
    order = json.loads((BASE / "call_order.json").read_text())["calls"]
    while True:
        built = 0
        for call in order:
            if built >= args.max_new:
                break
            outcome = build_one(call)
            if outcome not in ("not_generated", "invalid_output", "contaminated_tool_use"):
                built += 1
        finalized = len(list((BASE / "suites").glob("**/metadata.json")))
        if not args.follow or finalized == len(order):
            print(f"Build-eligible or recorded sources seen: {built}; generation finalized: {finalized}/390", flush=True)
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
