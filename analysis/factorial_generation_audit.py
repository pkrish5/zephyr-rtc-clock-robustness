#!/usr/bin/env python3
"""Audit frozen factorial generation cells, hashes, attempts, and token costs."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/spec_context_factorial_v1"
OUTPUT = ROOT / "results/spec_context_factorial_v1/generation_audit.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads((BASE / "lock.json").read_text())
    order_path = BASE / "call_order.json"
    if sha(order_path) != lock["call_order_sha256"]:
        raise ValueError("Call-order lock changed")
    order = json.loads(order_path.read_text())["calls"]
    rows = []
    totals = defaultdict(Counter)
    statuses = Counter()
    for call in order:
        model = call["model"].removeprefix("gpt-6-")
        run_id = f"{model}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
        directory = BASE / "suites" / model / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
        final = directory / "metadata.json"
        if not final.exists():
            statuses["pending"] += 1
            continue
        saved = json.loads(final.read_text())
        if any(saved[key] != call[key] for key in ("call_index", "model", "condition", "task_id", "sample_index", "prompt_sha256")):
            raise ValueError(f"Generation metadata mismatch: {run_id}")
        prompt = BASE / "prompts" / call["task_id"] / f"{call['condition']}.txt"
        if sha(prompt) != saved["prompt_sha256"]:
            raise ValueError(f"Prompt mismatch: {run_id}")
        if saved["source_sha256"]:
            source = directory / "test.c"
            if sha(source) != saved["source_sha256"]:
                raise ValueError(f"Source mismatch: {run_id}")
        attempts = sorted(directory.glob("attempt-*/attempt.json"))
        if len(attempts) != saved["attempts"]:
            raise ValueError(f"Attempt inventory mismatch: {run_id}")
        for path in attempts:
            attempt = json.loads(path.read_text())
            if attempt["prompt_sha256"] != saved["prompt_sha256"]:
                raise ValueError(f"Attempt prompt changed: {run_id}")
            for artifact, digest in (("events.jsonl", "events_sha256"), ("stderr.log", "stderr_sha256")):
                if sha(path.parent / artifact) != attempt[digest]:
                    raise ValueError(f"Raw attempt changed: {path}/{artifact}")
            if attempt["usage"]:
                for key, value in attempt["usage"].items():
                    totals[model][key] += value
        statuses[saved["status"]] += 1
        rows.append({"run_id": run_id, "call_index": call["call_index"],
                     "status": saved["status"], "attempts": len(attempts),
                     "source_sha256": saved["source_sha256"],
                     "usage": saved["usage"], "date_utc": saved["generation_date_utc"]})
    output = {"planned": len(order), "finalized": len(rows),
              "status_counts": dict(statuses), "token_totals_by_model": {k: dict(v) for k, v in totals.items()},
              "api_dollars": None, "api_dollars_note": "Authenticated Codex CLI did not expose billed dollars",
              "input_lock_sha256": sha(BASE / "lock.json"), "rows": rows}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Generation: {len(rows)}/{len(order)} finalized; statuses={dict(statuses)}; tokens={dict(totals)}")


if __name__ == "__main__":
    main()
