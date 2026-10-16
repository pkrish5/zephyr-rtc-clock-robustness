#!/usr/bin/env python3
"""Screen each frozen factorial source at nominal timing after source review.

This follower never runs a varied schedule. It waits for the serial generation,
build, and independent source-review records, and keeps every nominal verdict.
"""

import argparse
import json
import time

from nominal_factorial import BASE, RESULTS, ROOT, build_record, run_one


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-index", type=int, default=1)
    args = parser.parse_args()
    order = json.loads((BASE / "call_order.json").read_text())["calls"]
    for call in order:
        index = call["call_index"]
        if index < args.start_index:
            continue
        model = call["model"].removeprefix("gpt-6-")
        run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
        metadata = BASE / "suites" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}" / "metadata.json"
        while not metadata.exists() or build_record(run_id) is None:
            time.sleep(5)
        generation = json.loads(metadata.read_text())
        build = build_record(run_id)
        if generation["status"] != "generated" or build["status"] != "pass":
            print(f"{index:03d}/390 {run_id}: no nominal run ({generation['status']}, {build['status']})", flush=True)
            continue
        while True:
            path = ROOT / "analysis/factorial_source_decisions.json"
            review = json.loads(path.read_text())["decisions"].get(run_id)
            if review and review["functional"] != "pending" and review["timing_bound"] != "pending":
                break
            time.sleep(5)
        if review["source_sha256"] != build["source_sha256"]:
            raise ValueError(f"Source review/build hash mismatch: {run_id}")
        repeats = 5 if review["functional"] == "met" else 1
        for repeat in range(repeats):
            outcome = run_one(call, repeat)
            if outcome == "harness_error":
                print(f"{index:03d}/390 {run_id}: harness error retained; investigate", flush=True)
        print(f"{index:03d}/390 {run_id}: nominal gate complete ({repeats} repeats)", flush=True)
    print(f"Nominal follower finished; records in {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
