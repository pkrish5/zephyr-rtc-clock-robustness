#!/usr/bin/env python3
"""Audit the prespecified STM32 IWDG reset-state fidelity probe."""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = os.environ.get("IWDG_FIDELITY_VARIANT", "original")
if VARIANT not in ("original", "configured"):
    raise ValueError("Invalid IWDG fidelity variant")
RESULTS = ROOT / ("results/iwdg_fidelity" if VARIANT == "original" else
                  "results/iwdg_fidelity_configured")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    build_path = RESULTS / "build.json"
    build = json.loads(build_path.read_text())
    if build["exit_code"] != 0 or sha(ROOT / build["elf_path"]) != build["elf_sha256"]:
        raise ValueError("Frozen IWDG ELF changed or build failed")
    for path, expected in build["input_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"IWDG input changed: {path}")
    expected_ids = [f"iwdg-nominal-{i:03d}" for i in range(3)] + ["iwdg-min-000", "iwdg-max-000"]
    records = {}
    for run_id in expected_ids:
        path = RESULTS / "records" / f"{run_id}.json"
        if not path.exists():
            continue
        row = json.loads(path.read_text())
        if row["run_id"] != run_id or row["elf_sha256"] != build["elf_sha256"] or row["build_record_sha256"] != sha(build_path):
            raise ValueError(f"Frozen IWDG run mismatch: {run_id}")
        if row["cpu_performance_mips"] != 16 or row["systick_frequency_hz"] != 16000000 or row["quantum_ns"] != 1000:
            raise ValueError(f"Unexpected simulator settings: {run_id}")
        expected_hz = 32000 if row["condition"] == "nominal" else 17000 if row["condition"] == "min" else 47000
        if row["lsi_frequency_hz"] != expected_hz:
            raise ValueError(f"IWDG frequency mismatch: {run_id}")
        for artifact in ("platform", "uart", "monitor", "trace"):
            if row[artifact + "_sha256"] and sha(ROOT / row[artifact + "_path"]) != row[artifact + "_sha256"]:
                raise ValueError(f"IWDG artifact changed: {run_id}: {artifact}")
        trace = json.loads((ROOT / row["trace_path"]).read_text())
        if trace["outcome"] != row["outcome"]:
            raise ValueError(f"IWDG trace mismatch: {run_id}")
        records[run_id] = row
    complete = len(records) == 5
    def proper(row: dict) -> bool:
        return (row["outcome"] == "pass" and row["suite_start_count"] >= 2
                and row["testcase_passed_count"] >= 1
                and row["first_wait_virtual_ns"] is not None
                and row["first_testcase_pass_virtual_ns"] is not None
                and row["first_wait_virtual_ns"] < row["first_testcase_pass_virtual_ns"])
    nominal_ok = complete and all(proper(records[f"iwdg-nominal-{i:03d}"]) for i in range(3))
    endpoint_ok = complete and proper(records["iwdg-min-000"]) and proper(records["iwdg-max-000"])
    delays = {ident: (row["first_testcase_pass_virtual_ns"] - row["first_wait_virtual_ns"])
              for ident, row in records.items()
              if row["first_wait_virtual_ns"] is not None and row["first_testcase_pass_virtual_ns"] is not None}
    ordered = endpoint_ok and delays["iwdg-max-000"] < delays["iwdg-min-000"]
    output = {
        "variant": VARIANT,
        "protocol_path": "notes/IWDG_FIDELITY_PROTOCOL.md",
        "protocol_sha256": sha(ROOT / "notes/IWDG_FIDELITY_PROTOCOL.md"),
        "build_record_sha256": sha(build_path), "expected_run_count": 5,
        "observed_run_count": len(records),
        "runs": {ident: {"outcome": row["outcome"],
                         "frequency_hz": row["lsi_frequency_hz"],
                         "suite_starts": row["suite_start_count"],
                         "testcase_passed_count": row["testcase_passed_count"],
                         "wait_to_pass_virtual_ns": delays.get(ident),
                         "record_sha256": sha(RESULTS / "records" / f"{ident}.json")}
                 for ident, row in records.items()},
        "three_nominal_reboots_and_retained_state": bool(nominal_ok),
        "two_endpoint_reboots_and_retained_state": bool(endpoint_ok),
        "endpoint_delay_ordered_by_frequency": bool(ordered),
        "passes_prespecified_fidelity_probe": bool(nominal_ok and endpoint_ok and ordered),
        "admission_requires_user_review": True,
    }
    path = RESULTS / "summary.json"
    path.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(f"IWDG fidelity: {len(records)}/5 probes, nominal={nominal_ok}, "
          f"endpoints={endpoint_ok}, ordered={ordered}, pass={output['passes_prespecified_fidelity_probe']}")


if __name__ == "__main__":
    main()
