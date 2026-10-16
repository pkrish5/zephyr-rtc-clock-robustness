#!/usr/bin/env python3
"""Run independent, fixed-prompt Codex CLI test generations and freeze outputs."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "generated/phase2/prompt_template.txt"
SCHEMA = ROOT / "generated/phase2/response.schema.json"
COHORT = os.environ.get("PHASE2_COHORT", "sol_pilot")
COHORT_PATHS = {
    "sol_pilot": ("subjects/phase2_tasks.json", "phase2"),
    "luna_primary": ("subjects/phase2_tasks.json", "phase2_luna"),
    "rtc_bound_supplement": ("subjects/phase2_rtc_bound_tasks.json", "phase2_rtc_bound"),
    "sol_comparison": ("subjects/phase2_tasks_v2.json", "phase2_sol_comparison"),
    "astra_comparison": ("subjects/phase2_tasks_v2.json", "phase2_astra_comparison"),
    "luna_rtc_extension": ("subjects/rtc_extension_tasks.json", "luna_rtc_extension"),
}
if COHORT not in COHORT_PATHS:
    raise RuntimeError(f"Unknown Phase 2 cohort: {COHORT}")
task_file, cohort_directory = COHORT_PATHS[COHORT]
TASKS = ROOT / task_file
BASE = ROOT / "generated" / cohort_directory
RESULTS = ROOT / "results" / cohort_directory
K = 5
PROMPT_TRANSPORT = ("argument" if COHORT in
                    ("luna_rtc_extension", "sol_comparison", "astra_comparison")
                    else "stdin")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(content)


def load_manifest(model: str) -> dict:
    BASE.mkdir(parents=True, exist_ok=True)
    candidate = {
        "schema_version": 1,
        "k": K,
        "model_requested": model,
        "task_manifest_sha256": sha256(TASKS),
        "prompt_template_sha256": sha256(TEMPLATE),
        "response_schema_sha256": sha256(SCHEMA),
        "codex_cli_version": subprocess.check_output(["codex", "-V"], text=True).strip(),
        "zephyr_commit": json.loads(TASKS.read_text())["zephyr_commit"],
    }
    if COHORT != "sol_pilot":
        candidate["cohort"] = COHORT
    path = BASE / "generation_manifest.json"
    if path.exists():
        saved = json.loads(path.read_text())
        if saved != candidate:
            raise RuntimeError("Frozen model, tasks, prompt, schema, or CLI version changed")
        return saved
    write_new(path, json.dumps(candidate, indent=2, sort_keys=True) + "\n")
    return candidate


def render(task: dict, tasks: dict) -> str:
    template = TEMPLATE.read_text()
    oracle_bullets = "\n".join(f"- {item}" for item in task["required_oracles"])
    return template.format(feature_spec=task["feature_spec"],
                           oracle_bullets=oracle_bullets,
                           api_hints=task["api_hints"],
                           build_conf=task["build_conf"].rstrip())


def parse_events(path: Path) -> tuple[dict | None, int, list[dict], list[str], list[str]]:
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    usage_seen = False
    tool_calls = []
    server_models = []
    errors = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append("non-JSON CLI event")
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage_seen = True
            for key in usage:
                usage[key] += event["usage"].get(key, 0)
        if event.get("type") in ("item.started", "item.completed"):
            item = event.get("item", {})
            if item.get("type") in ("command_execution", "file_change", "web_search", "mcp_tool_call"):
                tool_calls.append({"event_type": event["type"], "item_type": item.get("type"),
                                   "command": item.get("command")})
        if event.get("type") in ("thread.started", "turn.started") and event.get("model"):
            server_models.append(event["model"])
        if event.get("type") == "error":
            errors.append(str(event.get("message", event)))
    return (usage if usage_seen else None), len(tool_calls), tool_calls, sorted(set(server_models)), errors


def run_one(task: dict, tasks: dict, index: int, model: str) -> bool:
    run_id = f"{task['id']}-r{index:02d}"
    run_dir = BASE / "suites" / task["id"] / f"r{index:02d}"
    final = run_dir / "metadata.json"
    prompt = render(task, tasks)
    if final.exists():
        metadata = json.loads(final.read_text())
        if metadata["prompt_sha256"] != hashlib.sha256(prompt.encode()).hexdigest():
            raise RuntimeError(f"Frozen prompt changed: {run_id}")
        print(f"{run_id}: already finalized ({metadata['status']})", flush=True)
        return True
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    if prompt_path.exists():
        if prompt_path.read_text() != prompt:
            raise RuntimeError(f"Prompt changed before retry: {run_id}")
    else:
        write_new(prompt_path, prompt)
    attempts = sorted(run_dir.glob("attempt-*/"))
    attempt = run_dir / f"attempt-{len(attempts) + 1:02d}"
    attempt.mkdir()
    events_path = attempt / "events.jsonl"
    stderr_path = attempt / "stderr.log"
    response_path = attempt / "response.json"
    started = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="phase2-generation-") as isolated:
        cmd = ["codex", "-a", "never", "exec", "--json", "--ephemeral", "--ignore-user-config",
               "--ignore-rules", "--skip-git-repo-check", "-C", isolated,
               "-s", "read-only", "-m", model,
               "--output-schema", str(SCHEMA), "-o", str(response_path),
               prompt if PROMPT_TRANSPORT == "argument" else "-"]
        try:
            with events_path.open("w") as stdout, stderr_path.open("w") as stderr:
                process = subprocess.run(cmd, input=prompt if PROMPT_TRANSPORT == "stdin" else None,
                                         text=True, stdout=stdout,
                                         stderr=stderr, timeout=600, check=False)
            returncode = process.returncode
            timeout = False
        except subprocess.TimeoutExpired:
            returncode = None
            timeout = True
    usage, tool_events, tool_calls, server_models, event_errors = parse_events(events_path)
    attempt_record = {
        "run_id": run_id,
        "cohort": COHORT,
        "attempt": len(attempts) + 1,
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "model_requested": model,
        "prompt_transport": PROMPT_TRANSPORT,
        "model_reported_by_events": server_models,
        "prompt_sha256": sha256(prompt_path),
        "returncode": returncode,
        "timeout": timeout,
        "usage": usage,
        "tool_event_count": tool_events,
        "tool_calls": tool_calls,
        "event_errors": event_errors,
        "events_path": str(events_path.relative_to(ROOT)),
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "response_path": str(response_path.relative_to(ROOT)) if response_path.exists() else None,
    }
    write_new(attempt / "attempt.json", json.dumps(attempt_record, sort_keys=True, indent=2) + "\n")
    if returncode != 0 or timeout:
        print(f"{run_id}: CLI infrastructure failure; attempt retained, stopped", flush=True)
        return False
    status = "generated"
    source_hash = None
    output_error = None
    if not response_path.exists():
        status, output_error = "invalid_output", "No response file"
    else:
        try:
            response = json.loads(response_path.read_text())
            if set(response) != {"test_c"} or not isinstance(response["test_c"], str) or not response["test_c"].strip():
                raise ValueError("Response lacks a nonempty test_c string")
            source = run_dir / "test.c"
            write_new(source, response["test_c"])
            source_hash = sha256(source)
        except (json.JSONDecodeError, ValueError) as exc:
            status, output_error = "invalid_output", str(exc)
    if tool_events:
        status = "contaminated_tool_use"
    metadata = {
        "run_id": run_id,
        "cohort": COHORT,
        "task_id": task["id"],
        "sample_index": index,
        "status": status,
        "output_error": output_error,
        "model_requested": model,
        "prompt_transport": PROMPT_TRANSPORT,
        "model_reported_by_events": server_models,
        "generation_date_utc": started,
        "prompt_sha256": sha256(prompt_path),
        "source_sha256": source_hash,
        "response_sha256": sha256(response_path) if response_path.exists() else None,
        "cli_version": subprocess.check_output(["codex", "-V"], text=True).strip(),
        "usage": usage,
        "api_dollar_cost": None,
        "api_dollar_cost_note": "ChatGPT-authenticated Codex CLI run; billed API dollars not exposed",
        "tool_event_count": tool_events,
        "attempts": len(attempts) + 1,
    }
    write_new(final, json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "generation.jsonl").open("a") as stream:
        stream.write(json.dumps(metadata, sort_keys=True) + "\n")
    print(f"{run_id}: {status} usage={usage}", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", help="One task id; omit to run all registered tasks")
    parser.add_argument("--index", type=int, help="One sample index 1..5; omit for all five")
    args = parser.parse_args()
    expected_model = {"sol_comparison": "gpt-6-sol", "astra_comparison": "gpt-6-astra",
                      "luna_rtc_extension": "gpt-6-luna"}.get(COHORT)
    if expected_model and args.model != expected_model:
        parser.error(f"{COHORT} requires {expected_model}")
    tasks = json.loads(TASKS.read_text())
    by_id = {task["id"]: task for task in tasks["tasks"]}
    expected_tasks = (1 if COHORT == "rtc_bound_supplement" else
                      2 if COHORT == "luna_rtc_extension" else
                      13 if COHORT in ("sol_comparison", "astra_comparison") else 11)
    if len(by_id) != expected_tasks:
        raise RuntimeError(f"Expected exactly {expected_tasks} registered tasks")
    if args.task and args.task not in by_id:
        parser.error("Unknown task id")
    if args.index is not None and args.index not in range(1, K + 1):
        parser.error("Index must be 1..5")
    load_manifest(args.model)
    selected = [by_id[args.task]] if args.task else tasks["tasks"]
    indices = [args.index] if args.index is not None else range(1, K + 1)
    for task in selected:
        for index in indices:
            if not run_one(task, tasks, index, args.model):
                return


if __name__ == "__main__":
    main()
