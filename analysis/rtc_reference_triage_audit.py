#!/usr/bin/env python3
"""Audit the approved reference-oracle union and derive conservative triage."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_reference_triage_access"
ORIGINAL = ROOT / "results/rtc_factorial_v2"
OUT = ROOT / "analysis/rtc_reference_triage_classification.json"
REPORT = ROOT / "notes/RTC_REFERENCE_TRIAGE_RESULT.md"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    m = read(BASE / "manifest.json")
    original_classes = {r["run_id"]: r for r in read(
        ROOT / "analysis/rtc_factorial_v2_classification.json")["rows"]}
    expected = {(family, "nominal", None) for family in m["selected_seed_union"]}
    expected |= {(family, endpoint, None) for family in m["selected_seed_union"]
                 for endpoint in ("min", "max")}
    expected |= {(family, "seeded", seed) for family, seeds in
                 m["selected_seed_union"].items() for seed in seeds}
    observed = {}
    for path in (BASE / "records").glob("*.json"):
        r = read(path)
        key = (r["family"], r["condition"], r["seed"])
        if key in observed:
            raise RuntimeError(f"Duplicate reference result: {key}")
        if r["manifest_sha256"] != sha(BASE / "manifest.json"):
            raise RuntimeError(f"Reference manifest mismatch: {key}")
        for kind in ("trace", "uart", "monitor"):
            if sha(ROOT / r[f"{kind}_path"]) != r[f"{kind}_sha256"]:
                raise RuntimeError(f"Reference artifact changed: {key} {kind}")
        observed[key] = (r, sha(path))
    missing = sorted(expected - set(observed))
    extra = sorted(set(observed) - expected)
    if extra:
        raise RuntimeError(f"Unregistered reference records: {extra}")
    controls = {key: observed[key][0]["outcome"] for key in expected
                if key[1] != "seeded" and key in observed}
    reference_outcomes = Counter(r["outcome"] for r, _ in observed.values())
    challenges = [r for r, _ in observed.values() if r["condition"] != "nominal"]
    challenge_wall_sum = sum(r["wall_seconds"] for r in challenges)
    completion_times = [datetime.fromisoformat(r["timestamp_utc"]) for r in challenges]
    challenge_completion_span = ((max(completion_times) - min(completion_times)).total_seconds()
                                 if completion_times else None)
    decisions = []
    for path in sorted((ORIGINAL / "records").glob("*.json")):
        row = read(path)
        if row["outcome"] != "fail":
            continue
        ref_key = (row["family"], row["condition"], row["seed"])
        ref = observed.get(ref_key)
        old = original_classes[row["run_id"]]
        if ref is None:
            revised = "unknown"
            reason = "Matching reference run missing"
        elif ref[0]["outcome"] != "pass":
            revised = "unknown"
            reason = f"Matching reference outcome {ref[0]['outcome']}; firmware/model cause unresolved"
        elif old["classification"] == "brittle_test_assumption" and old["persisted_replay_identical"]:
            revised = "brittle_test_assumption"
            reason = "Matching reference passes; source-backed legal-clock shortfall and identical original replay retained"
        else:
            revised = "unknown"
            reason = "Passing reference alone cannot classify a different failure"
        decisions.append({"run_id": row["run_id"], "family": row["family"],
                          "original_classification": old["classification"],
                          "revised_classification": revised, "reason": reason,
                          "reference_key": ref_key,
                          "reference_outcome": ref[0]["outcome"] if ref else None,
                          "reference_record_sha256": ref[1] if ref else None})
    if len(decisions) != 112 or len(original_classes) != 112:
        raise RuntimeError("Original classification coverage changed")
    result = {"status": "complete" if not missing else "incomplete",
              "manifest_sha256": sha(BASE / "manifest.json"),
              "registered_challenges": len(expected) - 3,
              "nominal_controls": 3, "observed_records": len(observed),
              "missing_reference_keys": missing,
              "reference_outcomes": dict(reference_outcomes),
              "challenge_serial_wall_seconds": round(challenge_wall_sum, 1),
              "first_to_last_challenge_completion_seconds": round(challenge_completion_span, 1),
              "control_outcomes": {str(k): v for k, v in sorted(controls.items())},
              "before": dict(Counter(d["original_classification"] for d in decisions)),
              "after": dict(Counter(d["revised_classification"] for d in decisions)),
              "decisions": decisions}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    by_family = defaultdict(Counter)
    for d in decisions:
        by_family[d["family"]][d["revised_classification"]] += 1
    lines = ["# Reduced RTC reference-oracle triage — 2026-10-06 UTC", "",
             f"Status: **{result['status']}**. Registered challenges: {len(expected)-3} "
             f"(69 failed-seed union plus six endpoints), with three separate nominal controls. "
             f"Observed records: {len(observed)}. Missing: {len(missing)}.", "",
             "The three references use the same frozen task specifications, an observable wait, "
             "a 26-second experimental ceiling, and an early-firing check. Their source and ELF "
             "hashes are in the [access-retry manifest](../results/rtc_reference_triage_access/manifest.json). "
             "The first nominal attempts in the earlier namespace crashed at virtual zero "
             "because the sandbox denied Renode history writes; those raw records remain intact. "
             "The access-retry series uses the same ELFs.", "",
             f"Reference outcomes: {dict(reference_outcomes)}. Classification before: "
             f"{result['before']}; after: {result['after']}.", "",
             f"The {len(challenges)} registered challenges consumed {challenge_wall_sum:.1f} "
             f"summed process wall seconds ({challenge_wall_sum/60:.1f} serial machine-minutes). "
             f"With three task-disjoint workers, the first-to-last completion span was "
             f"{challenge_completion_span:.1f} seconds (about {challenge_completion_span/60:.1f} minutes); "
             "initial startup adds a small amount. This is an observed runtime, not a simulation-time bound.", "",
             "| Task | Retained brittle assumption | Unknown after reference |",
             "| --- | ---: | ---: |"]
    for family, count in sorted(by_family.items()):
        lines.append(f"| {family} | {count['brittle_test_assumption']} | {count['unknown']} |")
    lines += ["", "A passing reference supports the specific clock-threshold attribution "
              "only alongside the frozen assertion and identical original replay. A reference "
              "failure or missing result changes the corresponding flip to unknown. This is "
              "simulation triangulation, not physical-hardware proof. No original verdict, "
              "trace, or earlier classification ledger was rewritten; the [row-level before/after "
              "ledger](../analysis/rtc_reference_triage_classification.json) retains every case.", ""]
    REPORT.write_text("\n".join(lines))
    print(f"Reference triage {result['status']}: {len(observed)}/{len(expected)} records, "
          f"before {result['before']}, after {result['after']}")


if __name__ == "__main__":
    main()
