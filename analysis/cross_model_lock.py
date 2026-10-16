#!/usr/bin/env python3
"""Freeze/audit input hashes for the preregistered three-model comparison."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "generated/cross_model/lock.json"
INPUTS = [
    "generated/cross_model/PROTOCOL.md",
    "generated/phase2/PROTOCOL.md",
    "subjects/phase2_tasks.json",
    "generated/phase2/prompt_template.txt",
    "generated/phase2/response.schema.json",
    "harness/phase2/generate.py",
    "harness/phase2/build_nominal.py",
    "analysis/phase2_summary.py",
    "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md",
    "analysis/phase2_split_gate_decisions.json",
    "subjects/phase3_hsi_100mips/plan.json",
    "subjects/phase3_rtc/plan.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    expected = {
        "registered_date": "2026-09-29", "schema_version": 1,
        "model_ids": ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"],
        "task_count": 11, "generations_per_task": 5,
        "exclude_sol_feasibility_pilot": True,
        "exclude_rtc_bound_context_supplement_from_model_comparison": True,
        "input_sha256": {path: sha(ROOT / path) for path in INPUTS},
    }
    if LOCK.exists():
        if json.loads(LOCK.read_text()) != expected:
            raise ValueError("Cross-model preregistration inputs changed")
        verb = "Audited"
    else:
        LOCK.write_text(json.dumps(expected, sort_keys=True, indent=2) + "\n")
        verb = "Frozen"
    print(f"{verb} cross-model lock: {sha(LOCK)}")


if __name__ == "__main__":
    main()
