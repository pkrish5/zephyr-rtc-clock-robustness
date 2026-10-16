#!/usr/bin/env python3
"""Account for the one operator-interrupted CLI attempt without editing raw logs."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/spec_context_factorial_v1"
RUN_ID = "luna-range_absent-workq-r02"
DIRECTORY = BASE / "suites/luna/range_absent/workq/r02"
ATTEMPT = DIRECTORY / "attempt-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def main():
    target = ATTEMPT / "attempt.json"
    if target.exists():
        raise FileExistsError(target)
    metadata = json.loads((DIRECTORY / "metadata.json").read_text())
    if metadata["run_id"] != RUN_ID or metadata["call_index"] != 87 or metadata["attempts"] != 2:
        raise ValueError("Unexpected frozen generation metadata")
    events = ATTEMPT / "events.jsonl"
    stderr = ATTEMPT / "stderr.log"
    parsed = [json.loads(line) for line in events.read_text().splitlines()]
    if [event.get("type") for event in parsed] != ["thread.started", "turn.started"]:
        raise ValueError("Interrupted attempt has unexpected events or completed usage")
    if (ATTEMPT / "response.json").exists():
        raise ValueError("Interrupted attempt unexpectedly has response output")
    record = {
        "run_id": RUN_ID, "call_index": 87, "attempt": 1,
        "started_utc": timestamp(events.stat().st_birthtime),
        "ended_utc": timestamp(max(events.stat().st_mtime, stderr.stat().st_mtime)),
        "model_requested": "gpt-6-luna", "model_reported_by_events": [],
        "prompt_sha256": metadata["prompt_sha256"], "prompt_transport": "argument",
        "returncode": None, "timeout": False, "interrupted": True,
        "interruption_note": "Parent generator received operator Ctrl-C before subprocess.run returned; exact child exit code and consumption are unavailable.",
        "usage": None, "tool_calls": [],
        "event_errors": ["operator_interrupted_before_turn_completed"],
        "events_sha256": sha(events), "stderr_sha256": sha(stderr),
        "response_sha256": None,
    }
    with target.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"Recovered accounting for {RUN_ID} attempt 1: no completed usage event")


if __name__ == "__main__":
    main()
