#!/usr/bin/env python3
"""Freeze a prompt-balanced replacement sample; preserve the original lock."""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORECAST = ROOT / "analysis/rtc_threshold_sample_v1/forecast.json"
OLD_SAMPLE = ROOT / "analysis/rtc_threshold_sample_v1/sample.json"
OUT = ROOT / "analysis/rtc_threshold_sample_v2"
SEED = 20261004
REGISTERED_UTC = "2026-10-04T19:34:28+00:00"
QUOTAS = {
    "luna": {"range_absent": 2, "range_present": 2},
    "sol": {"range_absent": 3, "range_present": 3},
    "astra": {"range_absent": 2, "range_present": 2},
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
    forecast = json.loads(FORECAST.read_text())
    predictions = forecast["predictions"]
    assert len(predictions) == 66
    predictable = [item for item in predictions
                   if item["prediction_status"] == "clock_only_prediction"]
    not_predictable = [item for item in predictions
                       if item["prediction_status"] == "not_predictable"]
    assert len(predictable) == 30 and len(not_predictable) == 36
    by_id = {item["run_id"]: item for item in predictions}
    certainty = {item["run_id"] for item in predictable
                 if item["predicted_failure_count"] > 0}
    assert len(certainty) == 3
    strata = defaultdict(list)
    for item in predictable:
        strata[(item["model"], item["condition"], item["task_family"])].append(item["run_id"])
    assert len(strata) == 8

    rng = random.Random(SEED)
    sample = set(certainty)
    # Cover every available predictable model x prompt x task-family stratum.
    for stratum in sorted(strata):
        if not any(rid in sample for rid in strata[stratum]):
            sample.add(rng.choice(sorted(strata[stratum])))
    # Fill fixed prompt-balanced model quotas without replacement.
    for model in ("luna", "sol", "astra"):
        for condition in ("range_absent", "range_present"):
            current = sum(by_id[rid]["model"] == model and
                          by_id[rid]["condition"] == condition for rid in sample)
            needed = QUOTAS[model][condition] - current
            assert needed >= 0
            remaining = sorted(item["run_id"] for item in predictable
                               if item["model"] == model and item["condition"] == condition
                               and item["run_id"] not in sample)
            sample.update(rng.sample(remaining, needed))
    assert len(sample) == 14
    assert certainty <= sample
    assert all(any(rid in sample for rid in ids) for ids in strata.values())
    for model, conditions in QUOTAS.items():
        for condition, quota in conditions.items():
            assert sum(by_id[rid]["model"] == model and
                       by_id[rid]["condition"] == condition for rid in sample) == quota
    measured = sample | {item["run_id"] for item in not_predictable}
    assert len(measured) == 50
    unsampled = sorted({item["run_id"] for item in predictable} - sample)
    assert len(unsampled) == 16
    assert all(by_id[rid]["predicted_failure_count"] == 0 for rid in unsampled)

    plan = {
        "schema_version": 2, "registered_utc": REGISTERED_UTC,
        "status": "frozen replacement sample before any factorial RTC varied run",
        "supersedes_sample_sha256": digest(OLD_SAMPLE),
        "forecast_sha256": digest(FORECAST),
        "random_seed": SEED,
        "random_generator": "Python random.Random; sorted strata and candidate IDs",
        "sampling_rule": ("Certainty-include the three nonzero threshold predictions. "
                          "Draw one random suite in every uncovered predictable "
                          "model x prompt x family stratum. Fill fixed per-model "
                          "prompt quotas uniformly without replacement."),
        "prompt_quotas_by_model": QUOTAS,
        "sampled_predictable_run_ids": sorted(sample),
        "full_run_not_predictable_run_ids": sorted(item["run_id"] for item in not_predictable),
        "all_phase3_measured_run_ids": sorted(measured),
        "unsampled_prediction_only_run_ids": unsampled,
        "seeded_runs_per_measured_suite": 100,
        "endpoint_challenges_per_measured_suite": 2,
        "total_suites_to_measure_after_approval": 50,
        "total_primary_seeded_runs_after_approval": 5000,
        "total_endpoint_challenges_after_approval": 100,
        "agreement_criterion": ("Every sampled predictable suite must have 100 "
                                "evaluable original seeded verdicts, with its full "
                                "per-seed pass/fail vector exactly equal to the "
                                "frozen forecast. Counts alone are insufficient."),
        "fallback": ("Report, exactly replay, and classify any evaluable mismatch; "
                     "investigate it and propose sampling expansion to the user "
                     "before expanding. Preserve original harness errors as "
                     "non-evaluable and diagnose separately."),
    }
    sample_path = OUT / "sample.json"
    save_or_verify(sample_path, plan)
    lock = {"schema_version": 2, "registered_utc": REGISTERED_UTC,
            "forecast_sha256": digest(FORECAST),
            "superseded_sample_sha256": digest(OLD_SAMPLE),
            "sample_sha256": digest(sample_path),
            "generator_sha256": digest(Path(__file__))}
    save_or_verify(OUT / "lock.json", lock)
    print("Balanced RTC sample: 14 predictable selected; 36 not predictable full; "
          "50 measured after approval; 16 prediction-only")


if __name__ == "__main__":
    main()
