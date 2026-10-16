#!/usr/bin/env python3
"""Apply reviewed source/trace patterns to exact RTC failure replays.

Unexpected assertions remain pending for individual manual review. Divergent
replays are recorded as unknown, never silently recoded as passing tests.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "analysis/phase3_rtc_classification_decisions.json"
PATTERNS = {
    "upstream": ("test_alarm_callback.c:140", "callback_called_status not equal to true", 13),
    "luna_primary_r04": ("test.c:92", "elapsed_ms <= 15000 is false", 15),
}


def main() -> None:
    ledger = json.loads(DECISIONS.read_text())
    changed = 0
    unresolved = []
    for run_id, row in sorted(ledger["decisions"].items()):
        if row["classification"] != "pending":
            continue
        replay_path = ROOT / "results/phase3_rtc/replay_records" / f"{run_id}.json"
        if not replay_path.exists():
            unresolved.append((run_id, "no replay"))
            continue
        replay = json.loads(replay_path.read_text())
        if replay["run_id"] != run_id or replay["original_outcome"] != "fail":
            raise ValueError(f"Incorrect replay record: {run_id}")
        row["replay_record_path"] = str(replay_path.relative_to(ROOT))
        row["replay_identical"] = replay["identical_trace_and_verdict"]
        if not replay["identical_trace_and_verdict"]:
            row["classification"] = "unknown"
            row["evidence"] = ("Fresh-process replay diverged from the sampled raw trace or verdict; "
                               "the original failure is retained but its cause is unresolved.")
            row["reviewer"] = "Codex four-way review after fresh-process replay"
            changed += 1
            continue
        pattern = PATTERNS.get(row["version_id"])
        if pattern is None:
            unresolved.append((run_id, "new assertion family"))
            row["replay_record_path"] = None
            row["replay_identical"] = None
            continue
        file_line, assertion, deadline = pattern
        uart = (ROOT / row["uart_path"]).read_text(errors="replace")
        if file_line not in uart or assertion not in uart:
            unresolved.append((run_id, "assertion differs from reviewed family"))
            row["replay_record_path"] = None
            row["replay_identical"] = None
            continue
        hz = row["lsi_frequency_hz"]
        calendar_seconds = 320_000 / hz
        if calendar_seconds <= deadline:
            unresolved.append((run_id, "frequency does not establish slow-clock deadline miss"))
            row["replay_record_path"] = None
            row["replay_identical"] = None
            continue
        row["classification"] = "brittle_test_assumption"
        row["evidence"] = (
            f"Exact fresh-process trace and verdict replay. The selected assertion at {file_line} "
            f"requires the alarm callback/calendar state by {deadline} wall seconds. At this "
            f"registered legal LSI input of {hz} Hz, the pinned 128 × 250 prescaler gives "
            f"approximately {calendar_seconds:.3f} wall seconds for ten RTC calendar seconds "
            "before ISR/polling latency. The raw UART fails that deadline assertion, with no "
            "different firmware-behavior assertion. Phase 1 continuation probes showed late "
            "callback arrival in this Renode model; attribution is model-specific pending "
            "physical validation, with no evidence here of a firmware race or invalid schedule.")
        row["reviewer"] = "Codex four-way source/trace review after exact replay"
        changed += 1
    if changed:
        DECISIONS.write_text(json.dumps(ledger, sort_keys=True, indent=2) + "\n")
    print(f"Newly classified={changed}; still awaiting individual review={len(unresolved)}")
    for run_id, reason in unresolved:
        print(f"  {run_id}: {reason}")


if __name__ == "__main__":
    main()
