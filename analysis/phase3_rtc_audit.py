#!/usr/bin/env python3
"""Check completeness of the registered RTC schedules, replays, and four-way labels."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/phase3_rtc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    plan = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())
    summary = json.loads((RESULTS / "summary.json").read_text())
    ledger_path = ROOT / "analysis/phase3_rtc_classification_decisions.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"decisions": {}}
    missing = []
    for ident in plan["versions"]:
        for i in range(plan["nominal_repeats"]):
            if not (RESULTS / "records" / f"{ident}-nominal-{i:03d}.json").exists():
                missing.append(f"{ident}-nominal-{i:03d}")
        for i in range(plan["seed_count"]):
            if not (RESULTS / "records" / f"{ident}-seeded-{i:03d}.json").exists():
                missing.append(f"{ident}-seeded-{i:03d}")
        for endpoint in ("min", "max"):
            if not (RESULTS / "records" / f"{ident}-{endpoint}.json").exists():
                missing.append(f"{ident}-{endpoint}")
    failures = {}
    for path in (RESULTS / "records").glob("*.json"):
        run = json.loads(path.read_text())
        if run["condition"] == "seeded" and run["outcome"] == "fail":
            failures[run["run_id"]] = run
    unregistered = sorted(set(failures) - set(ledger["decisions"]))
    vanished = sorted(set(ledger["decisions"]) - set(failures))
    if vanished:
        raise ValueError(f"Classification contains non-flips: {vanished}")
    unreplayed, pending, categorized = [], [], Counter()
    for run_id, run in failures.items():
        decision = ledger["decisions"].get(run_id)
        replay_path = RESULTS / "replay_records" / f"{run_id}.json"
        if not replay_path.exists():
            unreplayed.append(run_id)
        else:
            replay = json.loads(replay_path.read_text())
            if replay["original_trace_sha256"] != run["trace_sha256"]:
                raise ValueError(f"Replay original trace changed: {run_id}")
            for artifact in ("uart", "monitor", "trace"):
                if replay[artifact + "_sha256"] is not None and sha256(ROOT / replay[artifact + "_path"]) != replay[artifact + "_sha256"]:
                    raise ValueError(f"Replay {artifact} hash changed: {run_id}")
        if decision is None or decision["classification"] == "pending":
            pending.append(run_id)
        else:
            categorized[decision["classification"]] += 1
    status = {
        "plan_sha256": sha256(ROOT / "subjects/phase3_rtc/plan.json"),
        "raw_record_count": summary["raw_record_count"],
        "missing_registered_runs": len(missing),
        "missing_run_ids": missing,
        "observed_seeded_flips": len(failures),
        "unregistered_flip_decisions": unregistered,
        "unreplayed_flips": unreplayed,
        "pending_flip_decisions": pending,
        "classified_flips": dict(categorized),
        "complete": not (missing or unregistered or unreplayed or pending),
    }
    (RESULTS / "validation.json").write_text(json.dumps(status, sort_keys=True, indent=2) + "\n")
    print(f"RTC audit: runs={status['raw_record_count']}, missing={len(missing)}, "
          f"flips={len(failures)}, unreplayed={len(unreplayed)}, pending={len(pending)}, "
          f"complete={status['complete']}")


if __name__ == "__main__":
    main()
