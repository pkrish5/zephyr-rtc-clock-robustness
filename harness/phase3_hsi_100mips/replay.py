#!/usr/bin/env python3
"""Fresh-process replay of every HSI pass-to-fail verdict; preserve originals."""

import hashlib
import json
from pathlib import Path

from run import RESULTS, ROOT, load_plan, run_one

REPLAY_ROOT = ROOT / "results/phase3_hsi_100mips/replay"
REPLAY_LEDGER = ROOT / "results/phase3_hsi_100mips/replay_records"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    plan = load_plan()
    REPLAY_LEDGER.mkdir(parents=True, exist_ok=True)
    originals = []
    for path in sorted((RESULTS / "records").glob("*.json")):
        row = json.loads(path.read_text())
        if row["condition"] in ("seeded", "min", "max") and row["outcome"] == "fail":
            originals.append(row)
    for original in originals:
        run_id = original["run_id"]
        decision_path = REPLAY_LEDGER / f"{run_id}.json"
        if decision_path.exists():
            prior = json.loads(decision_path.read_text())
            if prior["original_record_sha256"] != sha(RESULTS / "records" / f"{run_id}.json"):
                raise ValueError(f"Original record changed: {run_id}")
            continue
        rerun = run_one(plan, original["version_id"], original["condition"],
                        original["index"], root=REPLAY_ROOT)
        before = json.loads((ROOT / original["trace_path"]).read_text())
        after = json.loads((ROOT / rerun["trace_path"]).read_text())
        identical = (original["outcome"] == rerun["outcome"]
                     and original["uart_sha256"] == rerun["uart_sha256"]
                     and before == after)
        decision = {
            "run_id": run_id, "version_id": original["version_id"],
            "condition": original["condition"], "seed": original["seed"],
            "original_record_path": str((RESULTS / "records" / f"{run_id}.json").relative_to(ROOT)),
            "original_record_sha256": sha(RESULTS / "records" / f"{run_id}.json"),
            "replay_record_path": str((REPLAY_ROOT / "records" / f"{run_id}.json").relative_to(ROOT)),
            "replay_record_sha256": sha(REPLAY_ROOT / "records" / f"{run_id}.json"),
            "original_outcome": original["outcome"], "replay_outcome": rerun["outcome"],
            "identical_trace_and_verdict": identical,
        }
        decision_path.write_text(json.dumps(decision, sort_keys=True, indent=2) + "\n")
        print(f"{run_id}: replay {rerun['outcome']}, identical={identical}", flush=True)
    print(f"Replayed/audited {len(originals)} original failures", flush=True)


if __name__ == "__main__":
    main()
