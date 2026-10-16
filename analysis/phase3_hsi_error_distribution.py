#!/usr/bin/env python3
"""Audit HSI startup-error missingness against suite and registered clock input."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2_contingency, spearmanr

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "results/phase3_hsi_100mips/qualified/records"
OUTPUT = ROOT / "results/phase3_hsi_100mips/qualified/startup_error_distribution.json"


def tally(rows, key):
    groups = defaultdict(Counter)
    for row in rows:
        groups[str(key(row))]["error" if row["outcome"] == "harness_error" else "other"] += 1
    return {group: dict(counts) for group, counts in sorted(groups.items())}


def chi_square(groups):
    cells = [[v.get("error", 0), v.get("other", 0)] for v in groups.values()]
    result = chi2_contingency(cells)
    return {"chi2": float(result.statistic), "p": float(result.pvalue),
            "degrees_of_freedom": int(result.dof)}


def main():
    rows = [json.loads(path.read_text()) for path in RECORDS.glob("*.json")]
    if len(rows) != 4606:
        raise ValueError(f"Expected 4,606 qualified records; found {len(rows)}")
    errors = [row for row in rows if row["outcome"] == "harness_error"]
    if len(errors) != 88 or any(row["virtual_ns"] != 0 for row in errors):
        raise ValueError("Startup-error inventory changed")
    seeded = [row for row in rows if row["condition"] == "seeded"]
    if len(seeded) != 4300:
        raise ValueError("Expected 43 suites times 100 seeds")
    cpu = tally(seeded, lambda row: row["cpu_performance_mips"])
    task = tally(seeded, lambda row: row["task_id"])
    suite = tally(seeded, lambda row: row["version_id"])
    seed_decile = tally(seeded, lambda row: row["seed"] // 10)
    frequencies = sorted({row["hsi_frequency_hz"] for row in seeded})
    if len(frequencies) != 100:
        raise ValueError("Expected 100 registered distinct oscillator inputs")
    frequency_quartile = {hz: index // 25 + 1 for index, hz in enumerate(frequencies)}
    frequency_bins = tally(seeded, lambda row: frequency_quartile[row["hsi_frequency_hz"]])
    event = [int(row["outcome"] == "harness_error") for row in seeded]
    freq = spearmanr([row["hsi_frequency_hz"] for row in seeded], event)
    seed_rank = spearmanr([row["seed"] for row in seeded], event)
    # A within-suite permutation keeps each suite's startup-error count fixed,
    # avoiding the false independent-run assumption in the analytic p-value.
    frequency_ranks = np.array([frequency_quartile[row["hsi_frequency_hz"]] for row in seeded], dtype=float)
    frequency_ranks -= frequency_ranks.mean()
    binary = np.array(event, dtype=float)
    observed = float(np.dot(frequency_ranks, binary))
    indices_by_suite = defaultdict(list)
    for index, row in enumerate(seeded):
        indices_by_suite[row["version_id"]].append(index)
    rng = np.random.default_rng(20261003)
    exceed = 0
    for _ in range(5000):
        permuted = binary.copy()
        for positions in indices_by_suite.values():
            permuted[positions] = rng.permutation(permuted[positions])
        exceed += abs(float(np.dot(frequency_ranks, permuted))) >= abs(observed)
    permutation_p = (exceed + 1) / 5001
    result = {
        "total_records": len(rows), "seeded_records": len(seeded),
        "startup_errors": len(errors), "seeded_startup_errors": sum(event),
        "nominal_startup_errors": sum(row["condition"] == "nominal" for row in errors),
        "by_cpu_mips": cpu, "by_task": task, "by_suite": suite,
        "by_seed_decile": seed_decile, "by_frequency_quartile": frequency_bins,
        "frequency_quartile_hz": {
            str(index+1): [frequencies[index*25], frequencies[index*25+24]]
            for index in range(4)},
        "chi_square_cpu": chi_square(cpu), "chi_square_frequency_quartile": chi_square(frequency_bins),
        "chi_square_task": chi_square(task),
        "chi_square_suite": chi_square(suite),
        "spearman_frequency": {"rho": float(freq.statistic), "p": float(freq.pvalue)},
        "within_suite_frequency_quartile_permutation": {
            "statistic": observed, "two_sided_p": permutation_p,
            "permutations": 5000, "random_seed": 20261003},
        "spearman_seed_index": {"rho": float(seed_rank.statistic), "p": float(seed_rank.pvalue)},
        "interpretation": "Descriptive post hoc tests; shared seeds and execution ordering violate simple independent-trial inference. No detectable monotone frequency trend; strong suite concentration.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("startup_errors", "by_cpu_mips", "chi_square_cpu", "chi_square_task", "spearman_frequency", "spearman_seed_index")}, indent=2))


if __name__ == "__main__":
    main()
