#!/usr/bin/env python3
"""Audit the initial RTC fault activations without scoring test suites."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_timing_mutants"
OUT = BASE / "activation_audit.json"
EXPECT = {
    ("rtc_alarm_callback", "early"): "alarm fired early",
    ("rtc_alarm_callback", "late"): "callbacks absent past legal-clock ceiling",
    ("rtc_time_counting", "early"): "calendar reached target too early",
    ("rtc_time_counting", "late"): "calendar did not reach target by ceiling",
    ("rtc_alarm_pending", "early"): "pending before fastest legal transition",
    ("rtc_alarm_pending", "late"): "pending absent past legal-clock ceiling",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((BASE / "manifest.json").read_text())
    rows = []
    for (family, mutant), assertion in sorted(EXPECT.items()):
        path = BASE / "activation_records" / f"activation-{family}-{mutant}.json"
        r = json.loads(path.read_text())
        uart = (ROOT / r["uart_path"]).read_text(errors="replace")
        platform = manifest["platforms"][mutant]
        valid = (r["outcome"] == "fail" and assertion in uart and
                 r["platform_sha256"] == platform["sha256"] and
                 sha(ROOT / r["platform_path"]) == platform["sha256"])
        rows.append({"family": family, "operator": mutant, "outcome": r["outcome"],
                     "expected_assertion": assertion, "activated": valid,
                     "record_sha256": sha(path)})
    never_path = BASE / "activation_records/activation-rtc_time_counting-never.json"
    never = json.loads(never_path.read_text())
    monitor = (ROOT / never["monitor_path"]).read_text(errors="replace")
    invalid = (never["outcome"] == "harness_error" and never["virtual_ns"] == 0 and
               "System.DivideByZeroException" in monitor)
    rows.append({"family": "rtc_time_counting", "operator": "never",
                 "outcome": never["outcome"], "activated": False,
                 "model_crash_confirmed": invalid, "record_sha256": sha(never_path)})
    if not all(row["activated"] for row in rows if row["operator"] != "never") or not invalid:
        raise RuntimeError("Activation evidence differs from expected assertions/crash")
    OUT.write_text(json.dumps({"status": "invalid_operator", "manifest_sha256": sha(BASE / "manifest.json"),
                               "suite_scoring_authorized": False, "rows": rows},
                              indent=2, sort_keys=True) + "\n")
    print("Six early/late task activations validated; 1-Hz nonfiring operator invalid")


if __name__ == "__main__":
    main()
