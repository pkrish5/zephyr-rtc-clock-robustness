#!/usr/bin/env python3
"""Complete source-only timing-premise review before new RTC schedules."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/rtc_extension_rq1_decisions.json"

JUDGMENTS = {
    "rtc_time_counting-r02": ("unknown", "The 22 s polling deadline exceeds the approximately 18.824 s slow-end calendar arrival by about 3.2 s, but the available task and kernel contracts do not bound all thread scheduling delay."),
    "rtc_time_counting-r03": ("unjustified", "Its 18 s observation cap is shorter than the approximately 18.824 s ten-calendar-second arrival permitted at 17 kHz LSI, even before poll phase and scheduling delay."),
    "rtc_time_counting-r04": ("unknown", "The 30 s calendar deadline leaves about 11 s beyond the legal slow-end arithmetic, but the full scheduling margin is not documented."),
    "rtc_time_counting-r05": ("unknown", "The 30 s calendar polling window exceeds the legal slow-end arithmetic; a full scheduling bound is unavailable. Its missing successive-monotonicity check is a separate functional-oracle issue."),
    "rtc_alarm_pending-r02": ("unknown", "The 20 one-second polling iterations narrowly exceed the approximately 18.824 s legal slow-end alarm arrival, but a complete scheduling/polling bound is unavailable. Build failure is a separate API-signature issue."),
    "rtc_alarm_pending-r03": ("unjustified", "After a 1 s wait it polls for at most 15 additional seconds, below the approximately 18.824 s needed for the legal 17 kHz RTC to reach an alarm ten calendar seconds ahead."),
    "rtc_alarm_pending-r04": ("unjustified", "The positive alarm check is forced after about 2 + 10 host seconds, shorter than the legal slow-end RTC arrival. The pre-alarm calendar predicate is separately wrong even at nominal timing."),
    "rtc_alarm_pending-r05": ("unknown", "The 2 + 20 s wait exceeds the legal slow-end arithmetic but has no complete documented polling/scheduling bound. Build failure is a separate API-signature issue."),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ledger = json.loads(OUTPUT.read_text())
    for run_id, (status, evidence) in JUDGMENTS.items():
        if run_id in ledger["decisions"]:
            raise ValueError(f"Already reviewed: {run_id}")
        task = run_id.rsplit("-r", 1)[0]
        source = ROOT / "generated/luna_rtc_extension/suites" / task / run_id.rsplit("-", 1)[1] / "test.c"
        metadata = json.loads((source.parent / "metadata.json").read_text())
        digest = sha(source)
        if digest != metadata["source_sha256"]:
            raise ValueError(f"Frozen source changed: {run_id}")
        ledger["decisions"][run_id] = {
            "task_id": task, "kind": "agent", "status": status,
            "issues": [evidence] if status == "unjustified" else [],
            "evidence": evidence,
            "reviewer": "Codex first-reviewer source coding under PHASE3_RQ1_CODING.md, before RTC-extension perturbation",
            "source_files_sha256": {str(source.relative_to(ROOT)): digest},
        }
    if len(ledger["decisions"]) != 12:
        raise ValueError("Expected two upstream and ten Luna extension units")
    ledger["status_note"] = (
        "First-reviewer source-only timing judgments for two upstream selected "
        "cases and ten frozen Luna sources. Keep separate from the blinded "
        "packet until independent labels are submitted. The five alarm Luna "
        "sources failed compilation, but remain in the RQ1 source denominator.")
    OUTPUT.write_text(json.dumps(ledger, sort_keys=True, indent=2) + "\n")
    print("Completed 12 RTC-extension source timing judgments")


if __name__ == "__main__":
    main()
