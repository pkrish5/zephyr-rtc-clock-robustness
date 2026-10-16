#!/usr/bin/env python3
"""Freeze exact 13-task/two-context prompts and 390-call order before generation."""

import hashlib
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/spec_context_factorial_v1"
TASKS = ROOT / "subjects/phase2_tasks_v2.json"
TEMPLATE = ROOT / "generated/phase2/prompt_template.txt"
SCHEMA = ROOT / "generated/phase2/response.schema.json"
PROTOCOL = BASE / "PROTOCOL.md"
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")
CONDITIONS = ("range_absent", "range_present")
SEED = 20261003
ENDING = 'Return a JSON object with exactly one field, "test_c"'
CONTEXT = {
    "hsi": "Documented hardware timing context: STM32F407 HSI nominal frequency is 16 MHz, with a specified accuracy of ±1% at 25 °C (15.84–16.16 MHz). This clock bound alone does not specify an ISR-to-thread delivery-latency bound.\n\n",
    "lsi_pilot": "Documented hardware timing context: STM32F407 LSI frequency is characterized from 17 to 47 kHz at 3 V over −40 to 105 °C. The selected RTC prescaler is fixed at 128 × 250, so the RTC calendar rate follows that oscillator range. This clock bound alone does not specify an ISR-to-thread delivery-latency bound.\n\n",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_or_check(path, value):
    raw = value.encode() if isinstance(value, str) else value
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"Frozen input changed: {path}")
    else:
        path.write_bytes(raw)


def main():
    tasks = json.loads(TASKS.read_text())["tasks"]
    if len(tasks) != 13 or len({task["id"] for task in tasks}) != 13:
        raise ValueError("Expected exact 13-task manifest")
    template = TEMPLATE.read_text()
    if template.count(ENDING) != 1:
        raise ValueError("Template ending changed")
    prompt_hashes = {}
    for task in tasks:
        baseline = template.format(
            feature_spec=task["feature_spec"],
            oracle_bullets="\n".join(f"- {item}" for item in task["required_oracles"]),
            api_hints=task["api_hints"], build_conf=task["build_conf"].rstrip())
        for condition in CONDITIONS:
            prompt = baseline if condition == "range_absent" else baseline.replace(
                ENDING, CONTEXT[task["arm"]] + ENDING)
            relative = f"prompts/{task['id']}/{condition}.txt"
            path = BASE / relative
            write_or_check(path, prompt)
            prompt_hashes[f"{task['id']}/{condition}"] = sha(path)
    rng = random.Random(SEED)
    calls = []
    for repeat in range(1, 6):
        task_ids = [task["id"] for task in tasks]
        rng.shuffle(task_ids)
        for task_id in task_ids:
            models = list(MODELS)
            rng.shuffle(models)
            for model in models:
                conditions = list(CONDITIONS)
                rng.shuffle(conditions)
                for condition in conditions:
                    calls.append({"call_index": len(calls) + 1, "task_id": task_id,
                                  "model": model, "condition": condition,
                                  "sample_index": repeat,
                                  "prompt_sha256": prompt_hashes[f"{task_id}/{condition}"]})
    if len(calls) != 390 or len({(c["task_id"], c["model"], c["condition"], c["sample_index"]) for c in calls}) != 390:
        raise ValueError("Unbalanced factorial")
    order_path = BASE / "call_order.json"
    write_or_check(order_path, json.dumps({"seed": SEED, "shuffle_algorithm": "Python random.Random.shuffle, task then model then condition, within each replicate", "calls": calls}, indent=2, sort_keys=True) + "\n")
    runner = ROOT / "harness/phase2/generate_factorial.py"
    if not runner.exists():
        raise ValueError("Generation runner must exist before lock")
    lock = {
        "schema_version": 1, "registered_date": "2026-10-03",
        "task_count": 13, "model_ids": list(MODELS), "conditions": list(CONDITIONS),
        "samples_per_cell": 5, "intended_calls": 390,
        "prompt_sha256": prompt_hashes,
        "input_sha256": {str(p.relative_to(ROOT)): sha(p) for p in
                         (TASKS, TEMPLATE, SCHEMA, PROTOCOL, runner,
                          ROOT / "paper/PROPOSED_SPEC_IN_CONTEXT_AMENDMENT.md",
                          ROOT / "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md")},
        "call_order_sha256": sha(order_path),
        "cli_version": subprocess.check_output(["codex", "-V"], text=True).strip(),
        "context_text": CONTEXT,
    }
    write_or_check(BASE / "lock.json", json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print(f"Frozen {len(prompt_hashes)} prompts and {len(calls)} calls; lock audited")


if __name__ == "__main__":
    main()
