#!/usr/bin/env python3
"""Post-start recoding of reviewed sources for non-clock latency premises.

The original functional and timing-bound decisions are never modified. This
recoding uses their saved per-source evidence and explicit exceptions.
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/factorial_source_decisions.json"
GATE = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
OUT = ROOT / "analysis/factorial_latency_assumptions.csv"
REPORT = ROOT / "notes/FACTORIAL_LATENCY_ASSUMPTIONS.md"

# These four callback sources have a source-backed short oscillator window but
# no separate, definite delivery-latency oracle in the saved source review.
CLOCK_ONLY_CALLBACK = {
    f"luna-range_absent-rtc_alarm_callback-r{i:02d}" for i in (1, 2, 3, 5)
}
# These six pending sources have an oscillator-shortfall oracle; two other
# pending sources have small, unproved service margins and remain unknown.
CLOCK_ONLY_PENDING = {
    "astra-range_absent-rtc_alarm_pending-r05",
    "luna-range_absent-rtc_alarm_pending-r01",
    "luna-range_absent-rtc_alarm_pending-r02",
    "luna-range_absent-rtc_alarm_pending-r04",
    "sol-range_absent-rtc_alarm_pending-r01",
    "sol-range_absent-rtc_alarm_pending-r03",
}
MARGIN_UNKNOWN_PENDING = {
    "astra-range_absent-rtc_alarm_pending-r02",
    "sol-range_absent-rtc_alarm_pending-r02",
}
LATENCY_FAMILIES = {
    "context": "pre/post worker completion observation or unsupported short service cutoff",
    "pending": "unprotected pre-expiry observation or worker scheduling/entry premise",
    "sleep": "worker-entry inference or ISR/thread service cutoff without a full latency bound",
    "timer_api": "expiry/status observation can race asynchronous timer progress",
    "workq": "unprotected pending/handler observation or worker service cutoff",
    "rtc_time_counting": "first calendar read assumes bounded set-to-read latency",
}


def classify(decision):
    rid = decision["run_id"]
    family = decision["task_id"]
    timing = decision["timing_bound"]
    if timing == "no_issue_found":
        return "not_found", "saved review found no unsupported timing premise"
    if timing == "unknown":
        return "unknown", "saved timing review did not establish a definite latency verdict"
    if timing != "inadequate":
        raise ValueError((rid, timing))
    if rid in CLOCK_ONLY_CALLBACK or rid in CLOCK_ONLY_PENDING:
        return "not_found", "saved inadequate oracle is an oscillator/window premise, without a separately established latency premise"
    if rid in MARGIN_UNKNOWN_PENDING:
        return "unknown", "clock window leaves an unproved service margin, but no definite immediate-delivery check"
    if family == "rtc_alarm_pending":
        raise AssertionError(f"Unreviewed pending inadequate source: {rid}")
    if family == "rtc_alarm_callback":
        return "latency_assumption_not_exposed_by_clock_rate", "callback calendar second or thread observation assumes bounded ISR/read/delivery latency"
    if family in LATENCY_FAMILIES:
        return "latency_assumption_not_exposed_by_clock_rate", LATENCY_FAMILIES[family]
    raise AssertionError(f"Unreviewed inadequate source family: {rid} {family}")


def main():
    decisions = json.loads(SOURCE.read_text())["decisions"]
    gate = {row["run_id"]: row for row in json.loads(GATE.read_text())["rows"]}
    assert len(decisions) == len(gate) == 390
    rows = []
    for rid in sorted(decisions):
        decision = decisions[rid]
        assert rid in gate
        source = ROOT / decision["source_path"]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == decision["source_sha256"] == gate[rid]["source_sha256"], rid
        status, basis = classify(decision)
        rows.append({"run_id": rid, "model": decision["model"],
                     "prompt_condition": decision["condition"],
                     "task_family": decision["task_id"],
                     "amended_functional_eligible": gate[rid]["amended_functional_eligible"],
                     "latency_category": status, "coding_basis": basis,
                     "original_timing_bound": decision["timing_bound"],
                     "original_timing_evidence": decision["timing_evidence"],
                     "source_path": decision["source_path"], "source_sha256": digest,
                     "coding_provenance": "2026-10-05 post-start descriptive recoding"})
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = defaultdict(Counter)
    rtc_eligible = defaultdict(Counter)
    for row in rows:
        key = (row["model"].replace("gpt-6-", ""), row["prompt_condition"])
        counts[key][row["latency_category"]] += 1
        if row["task_family"].startswith("rtc_") and row["amended_functional_eligible"]:
            rtc_eligible[key][row["latency_category"]] += 1
    lines = ["# Non-clock latency assumptions in frozen factorial sources — 2026-10-05", "",
             "This is a **post-start descriptive recoding** of all 390 frozen sources,",
             "based on the existing source-review evidence. It does not alter the",
             "original functional or timing-bound labels. `yes` requires a",
             "specific unsupported observation/delivery window or asynchronous",
             "ordering premise: exact-second callback read, immediate state",
             "probe, inferred worker entry, short ISR/thread service cutoff,",
             "or timer/workqueue interleaving. A merely finite but generous",
             "deadline with no proved scheduler bound remains `unknown` when the",
             "original review was unknown. Clock-only shortfall without a distinct",
             "latency premise is `not_found` for this category. `Not_found` does",
             "not prove a suite latency-robust. The row CSV preserves every original",
             "source-review explanation and source hash.", "",
             "| Model | Prompt | Yes | Unknown | Not found | Total |",
             "|---|---|---:|---:|---:|---:|"]
    for key in sorted(counts):
        c = counts[key]
        yes = c["latency_assumption_not_exposed_by_clock_rate"]
        unk = c["unknown"]
        no = c["not_found"]
        lines.append(f"| {key[0]} | {key[1]} | {yes} | {unk} | {no} | {yes+unk+no} |")
    lines += ["", "## Functionally eligible RTC subset (pilot sampling frame)", "",
              "| Model | Prompt | Yes | Unknown | Not found | Eligible RTC |",
              "|---|---|---:|---:|---:|---:|"]
    for key in sorted(rtc_eligible):
        c = rtc_eligible[key]
        yes = c["latency_assumption_not_exposed_by_clock_rate"]
        unk = c["unknown"]
        no = c["not_found"]
        lines.append(f"| {key[0]} | {key[1]} | {yes} | {unk} | {no} | {yes+unk+no} |")
    lines += ["", "A 0/100 result from the clock-only LSI schedule does not clear",
              "this category. For example, `astra-range_absent-rtc_alarm_callback-r01`",
              "has an exact-second callback calendar oracle and had 100/100 seeded",
              "passes in its already completed v2 series. Its source assumption",
              "requires a separate delivery-latency challenge to evaluate.", "",
              "The historical bound-context supplement's immediate second",
              "`k_sem_take(..., K_NO_WAIT)` after the first asynchronous callback",
              "is a separately recorded example. It is outside the 390 factorial",
              "sources and every factorial rate denominator.", ""]
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {len(rows)} rows; yes={sum(row['latency_category'].startswith('latency_') for row in rows)}")


if __name__ == "__main__":
    main()
