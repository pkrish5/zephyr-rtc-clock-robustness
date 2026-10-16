#!/usr/bin/env python3
"""Freeze the approved 60-call Stage B callback inputs before generation."""

import hashlib
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/stage_b_callback_v1"
TASK = "rtc_alarm_callback"
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")
CONDITIONS = ("range_absent", "range_present", "loose_spec", "reminder_only")
SEED = 20261008
SOURCES = {
    "range_absent": ROOT / "generated/spec_context_factorial_v1/prompts/rtc_alarm_callback/range_absent.txt",
    "range_present": ROOT / "generated/spec_context_factorial_v1/prompts/rtc_alarm_callback/range_present.txt",
    "loose_spec": ROOT / "notes/STAGE_B_PROPOSED_PROMPTS/loose_spec/rtc_alarm_callback.txt",
    "reminder_only": ROOT / "notes/STAGE_B_PROPOSED_PROMPTS/reminder_only/rtc_alarm_callback.txt",
}
SCHEMA = ROOT / "generated/phase2/response.schema.json"
RUNNER = ROOT / "harness/phase2/generate_stage_b_callback.py"
PROTOCOL = BASE / "PROTOCOL.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_or_check(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"Frozen file changed: {path}")
    else:
        path.write_bytes(raw)


def main():
    if not RUNNER.exists() or not PROTOCOL.exists():
        raise RuntimeError("Protocol and generation runner must exist before freeze")
    prompt_hashes = {}
    source_hashes = {}
    for condition in CONDITIONS:
        source = SOURCES[condition]
        target = BASE / "prompts" / f"{condition}.txt"
        write_or_check(target, source.read_bytes())
        prompt_hashes[condition] = sha(target)
        source_hashes[str(source.relative_to(ROOT))] = sha(source)
    rng = random.Random(SEED)
    calls = []
    for repeat in range(1, 6):
        models = list(MODELS)
        rng.shuffle(models)
        for model in models:
            conditions = list(CONDITIONS)
            rng.shuffle(conditions)
            for condition in conditions:
                calls.append({
                    "call_index": len(calls) + 1,
                    "task_id": TASK,
                    "model": model,
                    "condition": condition,
                    "sample_index": repeat,
                    "prompt_sha256": prompt_hashes[condition],
                })
    if len(calls) != 60 or len({(c["model"], c["condition"], c["sample_index"]) for c in calls}) != 60:
        raise RuntimeError("Call order not balanced")
    order = BASE / "call_order.json"
    write_or_check(order, (json.dumps({"seed": SEED, "calls": calls}, indent=2, sort_keys=True) + "\n").encode())
    lock = {
        "schema_version": 1,
        "registered_date": "2026-10-08",
        "task_id": TASK,
        "model_ids": list(MODELS),
        "conditions": list(CONDITIONS),
        "samples_per_cell": 5,
        "intended_calls": 60,
        "prompt_sha256": prompt_hashes,
        "prompt_source_sha256": source_hashes,
        "call_order_sha256": sha(order),
        "response_schema_sha256": sha(SCHEMA),
        "generation_runner_sha256": sha(RUNNER),
        "protocol_sha256": sha(PROTOCOL),
        "cli_version": subprocess.check_output(["codex", "-V"], text=True).strip(),
        "result_namespace": "results/stage_b_callback_v1",
    }
    write_or_check(BASE / "lock.json", (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode())
    print(f"Frozen {len(prompt_hashes)} prompts and {len(calls)} calls; lock {sha(BASE / 'lock.json')}")


if __name__ == "__main__":
    main()
