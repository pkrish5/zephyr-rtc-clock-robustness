#!/usr/bin/env python3
"""Build immutable run records for the Phase 0 clock-tolerance experiment."""

import argparse
import hashlib
import json
import os
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fragile import run as run_fragile
from robust import run as run_robust
from session import RenodeSession


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "phase0"
FIRMWARE = ROOT / "subjects" / "phase0_stm32f4_systick" / "firmware.elf"
RENODE_DEFAULT = Path("/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode")
BASE_PLATFORM_RELATIVE = Path("platforms/cpus/stm32f4.repl")
MIN_HZ = 15_840_000
NOMINAL_HZ = 16_000_000
MAX_HZ = 16_160_000
TESTS = {"fragile": run_fragile, "robust": run_robust}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def frequency(condition: str, seed: int) -> int:
    return NOMINAL_HZ if condition == "nominal" else random.Random(seed).randint(MIN_HZ, MAX_HZ)


def platform_for(renode_bin: Path, hz: int) -> tuple[Path, str]:
    base = renode_bin.parent / BASE_PLATFORM_RELATIVE
    original = base.read_text(encoding="utf-8")
    needle = "systickFrequency: 72000000"
    if original.count(needle) != 1:
        raise RuntimeError("Renode's STM32F4 platform changed; inspect before running")
    configured = original.replace(needle, f"systickFrequency: {hz}")
    path = RESULTS / "platforms" / f"stm32f4_systick_{hz}.repl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != configured:
        raise RuntimeError(f"Saved platform changed: {path}")
    if not path.exists():
        path.write_text(configured, encoding="utf-8")
    return path, sha256(base)


def metadata(renode_bin: Path, base_hash: str) -> dict:
    version = subprocess.run([str(renode_bin), "--version"], check=True, capture_output=True, text=True).stdout.strip()
    return {
        "firmware_sha256": sha256(FIRMWARE),
        "test_sha256": {name: sha256(ROOT / "harness" / "phase0" / f"{name}.py") for name in TESTS},
        "renode_version": version,
        "renode_platform_base_sha256": base_hash,
        "quantum_ns": 1000,
        "frequency_bound_hz": [MIN_HZ, MAX_HZ],
        "bound_source": "STM32F407 datasheet DS8626 Rev 12, Table 34, HSI oscillator accuracy at 25 C: -1% to +1%",
    }


def record_one(session: RenodeSession, name: str, condition: str, seed: int, hz: int,
               platform: Path, common: dict, raw_log: Path) -> dict:
    passed = TESTS[name](session)
    trace = {
        "condition": condition,
        "seed": seed,
        "test": name,
        "frequency_hz": hz,
        "observations": list(session.trace),
        "final_irq_count": session.read_word(0x20000000),
        "passed": passed,
    }
    trace_path = RESULTS / "traces" / f"{condition}-{seed:03d}-{name}.json"
    if trace_path.exists():
        raise RuntimeError(f"Raw trace already exists: {trace_path}")
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "run_id": f"{condition}-{seed:03d}-{name}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "condition": condition,
        "seed": seed,
        "test": name,
        "frequency_hz": hz,
        "passed": passed,
        "firmware_sha256": common["firmware_sha256"],
        "test_sha256": common["test_sha256"][name],
        "renode_version": common["renode_version"],
        "renode_platform_base_sha256": common["renode_platform_base_sha256"],
        "platform_sha256": sha256(platform),
        "platform_path": str(platform.relative_to(ROOT)),
        "quantum_ns": common["quantum_ns"],
        "trace_path": str(trace_path.relative_to(ROOT)),
        "renode_log_path": str(raw_log.relative_to(ROOT)),
        "final_irq_count": trace["final_irq_count"],
    }


def run_batch(args, renode_bin: Path):
    existing = {item["run_id"]: item for item in load_jsonl(RESULTS / "runs.jsonl")}
    for condition in (["nominal", "perturbed"] if args.condition == "both" else [args.condition]):
        for seed in range(args.start, args.start + args.count):
            ids = [f"{condition}-{seed:03d}-{name}" for name in TESTS]
            if all(run_id in existing for run_id in ids):
                continue
            if any(run_id in existing for run_id in ids):
                raise RuntimeError(f"Incomplete paired run {condition} seed {seed}; inspect raw output")
            hz = frequency(condition, seed)
            platform, base_hash = platform_for(renode_bin, hz)
            common = metadata(renode_bin, base_hash)
            raw_log = RESULTS / "renode_logs" / f"{condition}-{seed:03d}.log"
            with RenodeSession(renode_bin, platform, FIRMWARE, raw_log) as session:
                first = record_one(session, "fragile", condition, seed, hz, platform, common, raw_log)
                session.restart_same_binary()
                second = record_one(session, "robust", condition, seed, hz, platform, common, raw_log)
            append_jsonl(RESULTS / "runs.jsonl", first)
            append_jsonl(RESULTS / "runs.jsonl", second)
            print(f"{condition} seed={seed:03d} hz={hz} fragile={first['passed']} robust={second['passed']}", flush=True)


def replay_one(seed: int, renode_bin: Path):
    condition, name = "perturbed", "fragile"
    run_id = f"{condition}-{seed:03d}-{name}"
    original = {item["run_id"]: item for item in load_jsonl(RESULTS / "runs.jsonl")}.get(run_id)
    if original is None:
        raise RuntimeError(f"No original run for {run_id}")
    if original["passed"]:
        raise RuntimeError(f"Original run {run_id} did not fail")
    hz = frequency(condition, seed)
    platform, base_hash = platform_for(renode_bin, hz)
    common = metadata(renode_bin, base_hash)
    if original["firmware_sha256"] != common["firmware_sha256"] or original["test_sha256"] != common["test_sha256"][name]:
        raise RuntimeError("Firmware or test changed since original run")
    original_trace = json.loads((ROOT / original["trace_path"]).read_text(encoding="utf-8"))
    raw_log = RESULTS / "replay_logs" / f"{run_id}.log"
    with RenodeSession(renode_bin, platform, FIRMWARE, raw_log) as session:
        passed = TESTS[name](session)
        replay_trace = {
            "condition": condition,
            "seed": seed,
            "test": name,
            "frequency_hz": hz,
            "observations": list(session.trace),
            "final_irq_count": session.read_word(0x20000000),
            "passed": passed,
        }
    identical = replay_trace == original_trace
    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "identical_trace_and_verdict": identical,
        "original_trace_sha256": sha256(ROOT / original["trace_path"]),
        "replay_trace": replay_trace,
        "renode_log_path": str(raw_log.relative_to(ROOT)),
    }
    prior = {item["run_id"] for item in load_jsonl(RESULTS / "replays.jsonl")}
    if run_id in prior:
        raise RuntimeError(f"Replay record already exists for {run_id}")
    append_jsonl(RESULTS / "replays.jsonl", record)
    print(f"replay seed={seed:03d} identical={identical}", flush=True)
    if not identical:
        raise RuntimeError(f"Replay diverged for {run_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["batch", "replay", "replay-all"])
    parser.add_argument("--condition", choices=["nominal", "perturbed", "both"], default="both")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    renode_bin = Path(os.environ.get("RENODE_BIN", RENODE_DEFAULT)).resolve()
    if not renode_bin.is_file():
        raise SystemExit(f"Renode executable missing: {renode_bin}")
    if not FIRMWARE.is_file():
        raise SystemExit(f"Firmware missing: {FIRMWARE}; run its build.sh first")
    if args.action == "batch":
        run_batch(args, renode_bin)
    elif args.action == "replay":
        if args.seed is None:
            parser.error("replay requires --seed")
        replay_one(args.seed, renode_bin)
    else:
        existing = {item["run_id"] for item in load_jsonl(RESULTS / "replays.jsonl")}
        failures = [item for item in load_jsonl(RESULTS / "runs.jsonl") if item["condition"] == "perturbed" and item["test"] == "fragile" and not item["passed"]]
        for item in failures:
            if item["run_id"] not in existing:
                replay_one(item["seed"], renode_bin)


if __name__ == "__main__":
    main()
