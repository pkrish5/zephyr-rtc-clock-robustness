#!/usr/bin/env python3
"""Run the frozen 390-call three-model/two-context factorial, resuming safely."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "generated/spec_context_factorial_v1"
SCHEMA = ROOT / "generated/phase2/response.schema.json"
ORDER = BASE / "call_order.json"
LOCK = BASE / "lock.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as file:
        file.write(content)


def check_lock():
    lock = json.loads(LOCK.read_text())
    order = json.loads(ORDER.read_text())
    if sha(ORDER) != lock["call_order_sha256"] or len(order["calls"]) != 390:
        raise ValueError("Call order/lock mismatch")
    for relative, expected in lock["input_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"Locked input changed: {relative}")
    for cell, expected in lock["prompt_sha256"].items():
        if sha(BASE / "prompts" / f"{cell}.txt") != expected:
            raise ValueError(f"Prompt changed: {cell}")
    if subprocess.check_output(["codex", "-V"], text=True).strip() != lock["cli_version"]:
        raise ValueError("CLI version changed")
    return order["calls"]


def parse_events(path):
    usage = None
    tool_calls = []
    reported_models = set()
    errors = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append("Non-JSON event")
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        if event.get("type") in ("item.started", "item.completed"):
            item = event.get("item", {})
            if item.get("type") in ("command_execution", "file_change", "web_search", "mcp_tool_call"):
                tool_calls.append({"event_type": event["type"], "item_type": item.get("type"),
                                   "command": item.get("command")})
        if event.get("model") and event.get("type") in ("thread.started", "turn.started"):
            reported_models.add(event["model"])
        if event.get("type") == "error":
            errors.append(str(event.get("message", event)))
    return usage, tool_calls, sorted(reported_models), errors


def run_one(call):
    cell = f"{call['task_id']}/{call['condition']}"
    prompt_path = BASE / "prompts" / f"{cell}.txt"
    if sha(prompt_path) != call["prompt_sha256"]:
        raise ValueError("Call prompt does not match frozen order")
    model_short = call["model"].removeprefix("gpt-6-")
    run_id = f"{model_short}-{call['condition']}-{call['task_id']}-r{call['sample_index']:02d}"
    run_dir = BASE / "suites" / model_short / call["condition"] / call["task_id"] / f"r{call['sample_index']:02d}"
    final = run_dir / "metadata.json"
    if final.exists():
        saved = json.loads(final.read_text())
        if saved["prompt_sha256"] != call["prompt_sha256"] or saved["call_index"] != call["call_index"]:
            raise ValueError(f"Frozen output metadata mismatch: {run_id}")
        return "already_final"
    run_dir.mkdir(parents=True, exist_ok=True)
    attempts = sorted(run_dir.glob("attempt-*/"))
    attempt = run_dir / f"attempt-{len(attempts)+1:02d}"
    attempt.mkdir()
    events = attempt / "events.jsonl"
    stderr = attempt / "stderr.log"
    response = attempt / "response.json"
    started = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="factorial-generation-") as isolated:
        cmd = ["codex", "-a", "never", "exec", "--json", "--ephemeral",
               "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check",
               "-C", isolated, "-s", "read-only", "-m", call["model"],
               "--output-schema", str(SCHEMA), "-o", str(response), prompt_path.read_text()]
        try:
            with events.open("w") as out, stderr.open("w") as err:
                proc = subprocess.run(cmd, stdout=out, stderr=err, timeout=600, check=False)
            returncode, timeout = proc.returncode, False
        except subprocess.TimeoutExpired:
            returncode, timeout = None, True
    usage, tool_calls, reported_models, event_errors = parse_events(events)
    attempt_record = {
        "run_id": run_id, "call_index": call["call_index"], "attempt": len(attempts)+1,
        "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
        "model_requested": call["model"], "model_reported_by_events": reported_models,
        "prompt_sha256": call["prompt_sha256"], "prompt_transport": "argument",
        "returncode": returncode, "timeout": timeout, "usage": usage,
        "tool_calls": tool_calls, "event_errors": event_errors,
        "events_sha256": sha(events), "stderr_sha256": sha(stderr),
        "response_sha256": sha(response) if response.exists() else None,
    }
    write_new(attempt / "attempt.json", json.dumps(attempt_record, indent=2, sort_keys=True) + "\n")
    if returncode != 0 or timeout:
        print(f"{call['call_index']:03d}/390 {run_id}: CLI failure; attempt retained", flush=True)
        return "infrastructure_failure"
    status, error, source_hash = "generated", None, None
    try:
        payload = json.loads(response.read_text())
        if set(payload) != {"test_c"} or not isinstance(payload["test_c"], str) or not payload["test_c"].strip():
            raise ValueError("Expected one nonempty test_c string")
        source = run_dir / "test.c"
        write_new(source, payload["test_c"])
        source_hash = sha(source)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        status, error = "invalid_output", str(exc)
    if tool_calls:
        status = "contaminated_tool_use"
    metadata = {
        **{key: call[key] for key in ("call_index", "task_id", "model", "condition", "sample_index", "prompt_sha256")},
        "run_id": run_id, "status": status, "output_error": error,
        "generation_date_utc": started, "model_reported_by_events": reported_models,
        "prompt_path": str(prompt_path.relative_to(ROOT)), "prompt_transport": "argument",
        "source_sha256": source_hash, "response_sha256": sha(response) if response.exists() else None,
        "cli_version": json.loads(LOCK.read_text())["cli_version"], "usage": usage,
        "api_dollar_cost": None, "api_dollar_cost_note": "Authenticated CLI does not expose billed dollars",
        "tool_event_count": len(tool_calls), "attempts": len(attempts)+1,
    }
    write_new(final, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"{call['call_index']:03d}/390 {run_id}: {status}; tokens={usage}", flush=True)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new", type=int, default=390)
    parser.add_argument("--start-index", type=int, default=1)
    args = parser.parse_args()
    calls = check_lock()
    completed = 0
    for call in calls:
        if call["call_index"] < args.start_index:
            continue
        if completed >= args.max_new:
            break
        result = run_one(call)
        if result == "infrastructure_failure":
            raise SystemExit(2)
        if result != "already_final":
            completed += 1
    print(f"Newly finalized {completed}; total finalized {len(list((BASE/'suites').glob('**/metadata.json')))} / 390", flush=True)


if __name__ == "__main__":
    main()
