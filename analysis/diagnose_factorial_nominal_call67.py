#!/usr/bin/env python3
"""Separate fresh-process diagnostic for call 67's virtual-zero harness errors.

The original nominal records are never changed or counted as passes.
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "results/spec_context_factorial_v1"
DIAGNOSTIC = ORIGINAL / "diagnostic_call67"
RUN_ID = "astra-range_absent-pending-r01"


def main():
    module_path = ROOT / "harness/phase2/nominal_factorial.py"
    spec = importlib.util.spec_from_file_location("nominal_factorial", module_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    original_records = []
    for repeat in range(5):
        path = ORIGINAL / "nominal_records" / f"{RUN_ID}-nominal-{repeat:03d}.json"
        record = json.loads(path.read_text())
        if record["outcome"] != ("pass" if repeat == 0 else "harness_error"):
            raise ValueError(f"Unexpected original record: {path}")
        original_records.append({"path": str(path.relative_to(ROOT)),
                                 "outcome": record["outcome"],
                                 "elf_sha256": record["elf_sha256"]})

    order = json.loads((ROOT / "generated/spec_context_factorial_v1/call_order.json").read_text())["calls"]
    call = next(item for item in order if item["call_index"] == 67)
    build = json.loads((ORIGINAL / "build_records" / f"{RUN_ID}.json").read_text())
    if build["status"] != "pass":
        raise ValueError("Frozen build is not valid")
    runner.RESULTS = DIAGNOSTIC
    runner.build_record = lambda run_id: build if run_id == RUN_ID else None
    outcomes = [runner.run_one(call, repeat) for repeat in range(5)]
    summary = {"call_index": 67, "run_id": RUN_ID,
               "purpose": "infrastructure diagnostic only; originals remain gate verdicts",
               "original_records": original_records,
               "diagnostic_outcomes": outcomes,
               "diagnostic_record_dir": str((DIAGNOSTIC / "nominal_records").relative_to(ROOT))}
    DIAGNOSTIC.mkdir(parents=True, exist_ok=True)
    (DIAGNOSTIC / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"original": [r["outcome"] for r in original_records],
                      "diagnostic": outcomes}))


if __name__ == "__main__":
    main()
