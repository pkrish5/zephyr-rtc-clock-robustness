#!/usr/bin/env python3
"""Freeze source-derived RTC threshold hypotheses and a seeded validation sample.

This script reads frozen source/gate/schedule data only. It never launches Renode.
Once written, the forecast, sample, and lock are verified rather than replaced.
"""

import hashlib
import json
import random
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
PLAN = ROOT / "subjects/phase3_rtc/plan.json"
SOURCE_REVIEW = ROOT / "analysis/factorial_source_decisions.json"
OUTPUT = ROOT / "analysis/rtc_threshold_sample_v1"
SAMPLE_SEED = 20261004
SAMPLE_TARGET = 12
REGISTERED_UTC = "2026-10-04T19:29:18+00:00"

# Minimum accumulated host-time observation budget from the frozen source.
# The RTC counting task asks for a ten-calendar-second advance. Extra thread
# delays make count-based loops longer, not shorter; uptime loops are a
# clock-only hypothesis that the validation sample will test.
COUNTING_BUDGETS = {
    "sol-range_absent-rtc_time_counting-r01": (60, "600 x K_MSEC(100)"),
    "sol-range_present-rtc_time_counting-r01": (40, "uptime window 40000 ms"),
    "astra-range_absent-rtc_time_counting-r01": (40, "160 x K_MSEC(250)"),
    "astra-range_present-rtc_time_counting-r01": (20, "20 x K_MSEC(1000)"),
    "luna-range_present-rtc_time_counting-r01": (60, "60 x K_SECONDS(1)"),
    "luna-range_absent-rtc_time_counting-r01": (20, "uptime window 20 s"),
    "astra-range_absent-rtc_time_counting-r02": (40, "uptime window 40000 ms"),
    "astra-range_present-rtc_time_counting-r02": (30, "OBSERVATION_MS 30000"),
    "sol-range_present-rtc_time_counting-r02": (30, "300 x K_MSEC(100)"),
    "sol-range_absent-rtc_time_counting-r02": (30, "30 x K_MSEC(1000)"),
    "luna-range_absent-rtc_time_counting-r02": (30, "elapsed_ms window 30000"),
    "luna-range_present-rtc_time_counting-r02": (60, "600 x K_MSEC(100)"),
    "astra-range_present-rtc_time_counting-r03": (20, "80 x K_MSEC(250)"),
    "astra-range_absent-rtc_time_counting-r03": (60, "600 x K_MSEC(100)"),
    "sol-range_present-rtc_time_counting-r03": (30, "300 x K_MSEC(100)"),
    "sol-range_absent-rtc_time_counting-r03": (45, "450 x K_MSEC(100)"),
    "luna-range_present-rtc_time_counting-r03": (60, "uptime window 60000 ms"),
    "luna-range_absent-rtc_time_counting-r03": (20, "elapsed_ms window 20000"),
    "sol-range_present-rtc_time_counting-r04": (40, "160 x K_MSEC(250)"),
    "sol-range_absent-rtc_time_counting-r04": (25, "100 x K_MSEC(250)"),
    "astra-range_present-rtc_time_counting-r04": (24, "240 x K_MSEC(100)"),
    "astra-range_absent-rtc_time_counting-r04": (60, "uptime window 60000 ms"),
    "luna-range_absent-rtc_time_counting-r05": (30, "30 x K_MSEC(1000)"),
    "astra-range_absent-rtc_time_counting-r05": (60, "uptime window 60000 ms"),
    "astra-range_present-rtc_time_counting-r05": (20, "200 x K_MSEC(100)"),
    "sol-range_absent-rtc_time_counting-r05": (30, "300 x K_MSEC(100)"),
    "sol-range_present-rtc_time_counting-r05": (30, "uptime window 30000 ms"),
}

# Simple peripheral-pending polls with a short *first* deadline. This is a
# falsifiable Renode clock-only model, not a silicon guarantee. Other pending
# paths have too many service/phase interactions for an exact count forecast.
PENDING_BUDGETS = {
    "sol-range_absent-rtc_alarm_pending-r01": (16, "uptime deadline 16000 ms after calendar reset"),
    "sol-range_absent-rtc_alarm_pending-r03": (15, "first calendar deadline 15000 ms; later pending wait is separate"),
    "astra-range_absent-rtc_alarm_pending-r05": (15, "overall pending deadline 15000 ms"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_or_verify(path, value):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text() != rendered:
            raise ValueError(f"Frozen file differs; do not overwrite: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(rendered)


def main():
    gate = json.loads(GATES.read_text())
    plan = json.loads(PLAN.read_text())
    frequencies = plan["seeded_frequencies_hz"]
    assert len(frequencies) == 100 and len(set(frequencies)) == 100
    assert all(17000 <= value <= 47000 for value in frequencies)
    selected = [row for row in gate["rows"] if row["amended_functional_eligible"]
                and row["task_id"].startswith("rtc_")]
    assert len(selected) == 66
    assert set(COUNTING_BUDGETS) == {row["run_id"] for row in selected
                                     if row["task_id"] == "rtc_time_counting"}
    assert set(PENDING_BUDGETS) <= {row["run_id"] for row in selected}
    predictions = []
    for row in sorted(selected, key=lambda item: item["call_index"]):
        rid = row["run_id"]
        source_path = (ROOT / "generated/spec_context_factorial_v1/suites" /
                       row["model"] / row["condition"] / row["task_id"] /
                       f"r{rid.rsplit('-r', 1)[1]}" / "test.c")
        assert digest(source_path) == row["source_sha256"]
        if rid in COUNTING_BUDGETS:
            budget_s, evidence = COUNTING_BUDGETS[rid]
            status = "clock_only_prediction"
            reason = ("Calendar progress to +10 RTC seconds with a finite observation "
                      "budget; no callback or pending-bit assertion. Clock-only "
                      "model assumes normal Zephyr sleep/poll service.")
        elif rid in PENDING_BUDGETS:
            budget_s, evidence = PENDING_BUDGETS[rid]
            status = "clock_only_prediction"
            reason = ("Short first deadline tests the ten-RTC-second alarm compare. "
                      "Clock-only Renode hypothesis assumes the peripheral pending "
                      "flag is observable promptly after the compare; validation "
                      "may falsify this assumption.")
        else:
            budget_s, evidence = None, None
            status = "not_predictable"
            if row["task_id"] == "rtc_alarm_callback":
                reason = ("Callback IRQ delivery, callback service, or cross-context "
                          "ordering is not bounded by LSI rate alone.")
            else:
                reason = ("Pending-bit observation has a non-decisive or multi-stage "
                          "deadline; peripheral service, setup, and polling latency "
                          "can determine the verdict independently of LSI rate.")
        failing = ([seed for seed, frequency in enumerate(frequencies)
                    if Fraction(320000, frequency) > budget_s]
                   if budget_s is not None else None)
        predictions.append({
            "run_id": rid, "call_index": row["call_index"],
            "model": row["model"], "condition": row["condition"],
            "task_family": row["task_id"], "source_sha256": row["source_sha256"],
            "elf_sha256": row["elf_sha256"],
            "source_path": str(source_path.relative_to(ROOT)),
            "prediction_status": status, "prediction_reason": reason,
            "clock_model": "10 RTC s at 32000/f_LSI host s; fail when arrival > budget",
            "budget_seconds": budget_s, "budget_source_expression": evidence,
            "predicted_failure_seeds": failing,
            "predicted_failure_count": len(failing) if failing is not None else None,
        })
    counts = Counter(item["prediction_status"] for item in predictions)
    assert counts == {"clock_only_prediction": 30, "not_predictable": 36}
    assert Counter(item["predicted_failure_count"] for item in predictions
                   if item["prediction_status"] == "clock_only_prediction") == {0: 27, 11: 1, 13: 2}
    forecast = {
        "schema_version": 1, "registered_utc": REGISTERED_UTC,
        "status": "frozen before any factorial varied timing run",
        "schedule_plan_sha256": digest(PLAN), "gate_summary_sha256": digest(GATES),
        "source_review_sha256": digest(SOURCE_REVIEW),
        "predictive_model_scope": "Renode clock-only hypothesis; not a hardware guarantee or measured outcome",
        "predictions": predictions,
    }
    forecast_path = OUTPUT / "forecast.json"
    save_or_verify(forecast_path, forecast)

    predictable = [item for item in predictions
                   if item["prediction_status"] == "clock_only_prediction"]
    certainty = {item["run_id"] for item in predictable
                 if item["predicted_failure_count"] > 0}
    assert len(certainty) == 3
    strata = defaultdict(list)
    for item in predictable:
        strata[(item["model"], item["condition"], item["task_family"])].append(item["run_id"])
    assert len(strata) == 8
    rng = random.Random(SAMPLE_SEED)
    sample = set(certainty)
    for stratum in sorted(strata):
        if not any(rid in sample for rid in strata[stratum]):
            sample.add(rng.choice(sorted(strata[stratum])))
    remainder = sorted({item["run_id"] for item in predictable} - sample)
    sample.update(rng.sample(remainder, SAMPLE_TARGET - len(sample)))
    assert len(sample) == SAMPLE_TARGET
    measured = sorted(sample | {item["run_id"] for item in predictions
                                if item["prediction_status"] == "not_predictable"})
    assert len(measured) == 48
    sample_plan = {
        "schema_version": 1, "registered_utc": REGISTERED_UTC,
        "forecast_sha256": digest(forecast_path), "random_seed": SAMPLE_SEED,
        "random_generator": "Python random.Random, choice sorted strata then sample sorted remainder",
        "sampling_rule": ("Certainty include all nonzero predicted-count suites; choose one "
                          "seeded-random suite in each still-uncovered model x "
                          "condition x task-family stratum; fill to 12 by seeded "
                          "uniform draw without replacement from remaining predictable suites."),
        "predictable_sample_size": SAMPLE_TARGET,
        "sampled_predictable_run_ids": sorted(sample),
        "full_run_not_predictable_run_ids": sorted(set(measured) - sample),
        "all_phase3_measured_run_ids": measured,
        "unsampled_prediction_only_run_ids": sorted({item["run_id"] for item in predictable} - sample),
        "seeded_runs_per_measured_suite": 100,
        "endpoint_challenges_per_measured_suite": 2,
        "total_suites_to_measure_after_approval": len(measured),
        "total_primary_seeded_runs_after_approval": 100 * len(measured),
        "total_endpoint_challenges_after_approval": 2 * len(measured),
        "agreement_criterion": ("For each sampled predictable suite, all 100 original "
                                "seeded runs must be evaluable and the observed "
                                "pass/fail vector must equal the frozen per-seed "
                                "prediction exactly. Counts alone are insufficient."),
        "fallback": ("Any evaluable mismatch is reported, replayed and classified; "
                     "investigate source/model/trace and propose whether to expand "
                     "sampling before any expansion. A harness error leaves validation "
                     "inconclusive, remains in original records, and triggers separate "
                     "diagnosis rather than a substituted pass."),
    }
    sample_path = OUTPUT / "sample.json"
    save_or_verify(sample_path, sample_plan)
    lock = {"schema_version": 1, "registered_utc": REGISTERED_UTC,
            "forecast_sha256": digest(forecast_path),
            "sample_sha256": digest(sample_path),
            "generator_sha256": digest(Path(__file__))}
    save_or_verify(OUTPUT / "lock.json", lock)
    print(f"RTC forecast: {len(predictions)} eligible; {counts['clock_only_prediction']} "
          f"predicted; {counts['not_predictable']} not predictable; "
          f"{len(sample)} sampled predictable; {len(measured)} to measure after approval")


if __name__ == "__main__":
    main()
