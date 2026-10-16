#!/usr/bin/env python3
"""Replay one nominal harness error separately, preserving its original verdict."""

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "results/spec_context_factorial_v1"
BASE = ROOT / "generated/spec_context_factorial_v1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--call-index", type=int, required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()

    order = json.loads((BASE / "call_order.json").read_text())["calls"]
    call = next(item for item in order if item["call_index"] == args.call_index)
    model = call["model"].removeprefix("gpt-6-")
    run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
    nominal_id = f"{run_id}-nominal-{args.repeat:03d}"
    original_path = ORIGINAL / "nominal_records" / f"{nominal_id}.json"
    original = json.loads(original_path.read_text())
    if original["outcome"] != "harness_error" or original["virtual_ns"] != 0:
        raise ValueError("Original is not a virtual-zero harness error")

    spec = importlib.util.spec_from_file_location(
        "nominal_factorial", ROOT / "harness/phase2/nominal_factorial.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    build = runner.build_record(run_id)
    if not build or build["status"] != "pass":
        raise ValueError("Frozen build is unavailable")
    diagnostic = ORIGINAL / f"diagnostic_call{args.call_index}_repeat{args.repeat:03d}"
    runner.RESULTS = diagnostic
    runner.build_record = lambda candidate: build if candidate == run_id else None
    outcome = runner.run_one(call, args.repeat)
    record_path = diagnostic / "nominal_records" / f"{nominal_id}.json"
    record = json.loads(record_path.read_text())
    if record["elf_sha256"] != original["elf_sha256"]:
        raise ValueError("Diagnostic ELF differs from original")
    summary = {
        "call_index": args.call_index,
        "repeat": args.repeat,
        "run_id": run_id,
        "purpose": "infrastructure diagnostic; original gate record is unchanged",
        "original_record": str(original_path.relative_to(ROOT)),
        "original_outcome": original["outcome"],
        "diagnostic_record": str(record_path.relative_to(ROOT)),
        "diagnostic_outcome": outcome,
        "elf_sha256": record["elf_sha256"],
    }
    (diagnostic / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"original": original["outcome"], "diagnostic": outcome}))


if __name__ == "__main__":
    main()
