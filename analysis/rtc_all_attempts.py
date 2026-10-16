#!/usr/bin/env python3
"""Read-only derivation of all-attempt factorial attrition and RTC outcomes.

The JSON output is analysis, not an experimental record. No simulator runs occur.
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "analysis/factorial_prephase3/model_condition_family.csv"
CLOCK = ROOT / "analysis/rtc_factorial_v2_final_summary.json"
MUTANTS = ROOT / "analysis/rtc_quality_mutant_scores/rows.csv"
OFFSETS = ROOT / "results/rtc_alarm_offset_v1/analysis_summary.json"
OUTPUT = ROOT / "analysis/rtc_all_attempts.json"


def gate_totals(rows):
    totals = Counter()
    for row in rows:
        for key in ("generated", "built", "source_functional_met", "functional_gate_eligible"):
            totals[key] += int(row[key])
    generated = totals["generated"]
    built = totals["built"]
    functional = totals["source_functional_met"]
    eligible = totals["functional_gate_eligible"]
    assert generated >= built >= functional >= eligible
    result = {
        "generated": generated,
        "build_fail": generated - built,
        "functional_fail_after_build": built - functional,
        "nominal_fail_after_functional": functional - eligible,
        "eligible": eligible,
    }
    assert sum(result[k] for k in (
        "build_fail", "functional_fail_after_build", "nominal_fail_after_functional", "eligible"
    )) == generated
    return result


def main():
    with GATES.open(newline="") as stream:
        gates = list(csv.DictReader(stream))
    clock = json.loads(CLOCK.read_text())
    offsets = json.loads(OFFSETS.read_text())
    with MUTANTS.open(newline="") as stream:
        mutants = list(csv.DictReader(stream))

    by_gate = defaultdict(list)
    by_rtc_gate = defaultdict(list)
    for row in gates:
        key = (row["model"], row["prompt_condition"])
        by_gate[key].append(row)
        if row["task_family"].startswith("RTC "):
            by_rtc_gate[key].append(row)

    by_clock = defaultdict(list)
    for suite in clock["suite_distribution"]:
        by_clock[(suite["model"], suite["prompt_condition"])].append(suite)

    by_late = defaultdict(list)
    for row in mutants:
        if row["kind"] == "ai" and row["operator"] == "late":
            by_late[(row["model"], row["prompt_condition"])].append(row)

    by_offset = defaultdict(list)
    for row in offsets["rows"]:
        if row["kind"] == "ai" and row["sign"] == 1 and row["family"] in (
            "rtc_alarm_callback", "rtc_alarm_pending"
        ):
            by_offset[(row["model"], row["prompt_condition"])].append(row)

    cells = []
    for model in ("luna", "sol", "astra"):
        for prompt in ("range_absent", "range_present"):
            key = (model, prompt)
            all_gates = gate_totals(by_gate[key])
            rtc_gates = gate_totals(by_rtc_gate[key])
            suites = by_clock[key]
            assert all_gates["generated"] == 65
            assert rtc_gates["generated"] == 15
            assert rtc_gates["eligible"] == len(suites)

            clock_fail = sum(s.get("fail", 0) > 0 for s in suites)
            complete_pass = sum(
                s["status"] == "measured" and s.get("fail", 0) == 0
                and s.get("missing", 0) == 0 for s in suites
            )
            prediction_only = sum(s["status"] == "prediction_only" for s in suites)
            incomplete_zero_fail = sum(
                s["status"] == "measured" and s.get("fail", 0) == 0
                and s.get("missing", 0) > 0 for s in suites
            )
            assert clock_fail + complete_pass + prediction_only + incomplete_zero_fail == len(suites)
            late = by_late[key]
            assert len(late) == len(suites)
            offset = by_offset[key]
            assert all(r["status"] in ("kill", "survive", "missing_verdict") for r in offset)
            cells.append({
                "model": model,
                "prompt_condition": prompt,
                "all_tasks": all_gates,
                "rtc_tasks": rtc_gates,
                "clock_fail_suites": clock_fail,
                "clock_complete_pass_suites": complete_pass,
                "clock_prediction_only_suites": prediction_only,
                "clock_incomplete_zero_fail_suites": incomplete_zero_fail,
                "robust_confirmed_share_all_rtc_attempts": complete_pass / 15,
                "robust_possible_upper_share_all_rtc_attempts": (
                    complete_pass + prediction_only + incomplete_zero_fail
                ) / 15,
                "slow_oscillator_kill": sum(r["kill"] == "yes" for r in late),
                "slow_oscillator_evaluable": sum(r["kill"] in ("yes", "no") for r in late),
                "late_alarm_offset_kill": sum(r["status"] == "kill" for r in offset),
                "late_alarm_offset_evaluable": sum(r["status"] in ("kill", "survive") for r in offset),
                "late_alarm_offset_missing": sum(r["status"] == "missing_verdict" for r in offset),
            })

    assert sum(c["all_tasks"]["generated"] for c in cells) == 390
    assert sum(c["rtc_tasks"]["generated"] for c in cells) == 90
    assert sum(c["rtc_tasks"]["eligible"] for c in cells) == 66
    assert sum(c["clock_fail_suites"] for c in cells) == 3
    assert sum(c["clock_prediction_only_suites"] for c in cells) == 16
    assert sum(c["late_alarm_offset_kill"] for c in cells) == 34
    result = {"scope": "13 generated tasks for all_tasks; three RTC tasks for rtc_tasks and outcomes", "cells": cells}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    for c in cells:
        a, r = c["all_tasks"], c["rtc_tasks"]
        print(c["model"], c["prompt_condition"],
              "all B/F/N/E", *(a[k] for k in ("build_fail", "functional_fail_after_build", "nominal_fail_after_functional", "eligible")),
              "RTC B/F/N/E", *(r[k] for k in ("build_fail", "functional_fail_after_build", "nominal_fail_after_functional", "eligible")),
              "clock flip/complete/pred/incomplete", *(c[k] for k in ("clock_fail_suites", "clock_complete_pass_suites", "clock_prediction_only_suites", "clock_incomplete_zero_fail_suites")),
              "fault late/offset", f'{c["slow_oscillator_kill"]}/{c["slow_oscillator_evaluable"]}',
              f'{c["late_alarm_offset_kill"]}/{c["late_alarm_offset_evaluable"]}')


if __name__ == "__main__":
    main()
