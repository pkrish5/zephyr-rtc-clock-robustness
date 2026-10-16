#!/usr/bin/env python3
"""Rerun HSI harness errors separately without replacing registered outcomes."""

import hashlib
import json
from pathlib import Path

from run import RESULTS, ROOT, load_plan, run_one

BASE = ROOT / "results/phase3_hsi_100mips"
DIAGNOSTICS = BASE / "diagnostics"
LEDGER = BASE / "diagnostic_records"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    plan = load_plan()
    LEDGER.mkdir(parents=True, exist_ok=True)
    errors = []
    for path in sorted((RESULTS / "records").glob("*.json")):
        row = json.loads(path.read_text())
        if row["outcome"] == "harness_error":
            errors.append((path, row))
    for original_path, original in errors:
        run_id = original["run_id"]
        ledger_path = LEDGER / f"{run_id}.json"
        if ledger_path.exists():
            prior = json.loads(ledger_path.read_text())
            if prior["original_record_sha256"] != sha(original_path):
                raise ValueError(f"Original harness error changed: {run_id}")
            continue
        rerun = run_one(plan, original["version_id"], original["condition"],
                        original["index"], root=DIAGNOSTICS)
        rerun_path = DIAGNOSTICS / "records" / f"{run_id}.json"
        row = {"run_id": run_id,
               "original_record_path": str(original_path.relative_to(ROOT)),
               "original_record_sha256": sha(original_path),
               "diagnostic_record_path": str(rerun_path.relative_to(ROOT)),
               "diagnostic_record_sha256": sha(rerun_path),
               "original_outcome": "harness_error", "diagnostic_outcome": rerun["outcome"],
               "original_virtual_ns": original["virtual_ns"],
               "diagnostic_virtual_ns": rerun["virtual_ns"],
               "disposition": "original remains non-evaluable regardless of diagnostic outcome"}
        ledger_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        print(f"{run_id}: diagnostic {rerun['outcome']}; original retained", flush=True)
    index = {path.stem: json.loads(path.read_text()) for path in sorted(LEDGER.glob("*.json"))}
    if set(index) != {row["run_id"] for _, row in errors}:
        raise ValueError("Diagnostic ledger does not match all qualified harness errors")
    (BASE / "diagnostic_summary.json").write_text(
        json.dumps({"diagnostics": index}, indent=2, sort_keys=True) + "\n")
    print(f"Audited {len(errors)} original harness errors", flush=True)


if __name__ == "__main__":
    main()
