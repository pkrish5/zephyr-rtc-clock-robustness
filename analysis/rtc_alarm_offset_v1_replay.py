#!/usr/bin/env python3
"""Replay activated alarm-suite kills without changing the original records."""

import json
import multiprocessing
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
from rtc_alarm_offset_v1 import OUT, validate, run_suite  # noqa: E402


def replay_partition(items):
    for rid, sign in items:
        run_suite(rid, sign, replay=True)


def main():
    m = validate()
    items = []
    for rid, suite in sorted(m["suites"].items()):
        if suite["kind"] == "reference" or suite["family"] == "rtc_time_counting":
            continue
        for sign, name in ((-1, "early"), (1, "late")):
            label = f"{rid}__{name}"
            path = OUT / "records" / f"{label}.json"
            if not path.exists():
                raise RuntimeError(f"Original missing: {label}")
            record = json.loads(path.read_text())
            uart_path = ROOT / record["uart_path"]
            uart = uart_path.read_text(errors="replace") if uart_path.exists() else ""
            if record["outcome"] == "fail" and f"QUALITY_ALARM_OFFSET id=" in uart:
                items.append((rid, sign))
    groups = [items[i::3] for i in range(3)]
    print(f"Replaying {len(items)} explicit activated failures in three disjoint partitions", flush=True)
    workers = [multiprocessing.Process(target=replay_partition, args=(group,)) for group in groups]
    for proc in workers:
        proc.start()
    for proc in workers:
        proc.join()
    if any(proc.exitcode != 0 for proc in workers):
        raise RuntimeError(f"Replay workers failed: {[proc.exitcode for proc in workers]}")


if __name__ == "__main__":
    main()
