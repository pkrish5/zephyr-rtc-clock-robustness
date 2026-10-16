#!/usr/bin/env python3
"""Derive Phase 0 counts, Wilson intervals, and four-way labels from raw logs."""

import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase0"
Z_975 = 1.959963984540054


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def wilson(successes, n):
    if not n:
        return None
    p = successes / n
    z2 = Z_975 * Z_975
    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    half = Z_975 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominator
    lower = max(0.0, center - half)
    if lower < 1e-15:
        lower = 0.0
    return [lower, min(1.0, center + half)]


def main():
    runs = load_jsonl(RESULTS / "runs.jsonl")
    replays = {item["run_id"]: item for item in load_jsonl(RESULTS / "replays.jsonl")}
    by_key = {(item["condition"], item["seed"], item["test"]): item for item in runs}
    if len(by_key) != len(runs):
        raise RuntimeError("Duplicate run IDs in raw log")
    expected = {(condition, seed, name) for condition in ("nominal", "perturbed") for seed in range(100) for name in ("fragile", "robust")}
    if set(by_key) != expected:
        missing = sorted(expected - set(by_key))
        unexpected = sorted(set(by_key) - expected)
        raise RuntimeError(f"Incomplete/extra runs: missing={missing[:5]}, unexpected={unexpected[:5]}")
    firmware_hashes = {item["firmware_sha256"] for item in runs}
    simulator_versions = {item["renode_version"] for item in runs}
    test_hashes = {name: {item["test_sha256"] for item in runs if item["test"] == name} for name in ("fragile", "robust")}
    if len(firmware_hashes) != 1 or len(simulator_versions) != 1 or any(len(v) != 1 for v in test_hashes.values()):
        raise RuntimeError("Frozen firmware/test or simulator version changed")
    if any(item["frequency_hz"] < 15_840_000 or item["frequency_hz"] > 16_160_000 for item in runs):
        raise RuntimeError("Frequency outside the documented Phase 0 bound")

    classifications = []
    rates = {}
    for name in ("fragile", "robust"):
        nominal_passes = sum(by_key[("nominal", seed, name)]["passed"] for seed in range(100))
        perturbed_passes = sum(by_key[("perturbed", seed, name)]["passed"] for seed in range(100))
        flips = 0
        for seed in range(100):
            nominal = by_key[("nominal", seed, name)]
            perturbed = by_key[("perturbed", seed, name)]
            if nominal["passed"] and not perturbed["passed"]:
                flips += 1
                replay = replays.get(perturbed["run_id"])
                companion = by_key[("perturbed", seed, "robust")]
                if (name == "fragile" and replay is not None and replay["identical_trace_and_verdict"]
                        and companion["passed"] and perturbed["final_irq_count"] == 0
                        and companion["final_irq_count"] == 1):
                    label = "brittle test assumption"
                    reason = "same frozen firmware emits the GPIO event within the event-wait deadline; fixed sleep observes before the SysTick ISR; fresh replay matches"
                else:
                    label = "unknown"
                    reason = "required replay or companion evidence is missing or inconsistent"
                classifications.append({"run_id": perturbed["run_id"], "seed": seed, "category": label, "reason": reason})
        rates[name] = {
            "nominal_passes_of_100": nominal_passes,
            "perturbed_passes_of_100": perturbed_passes,
            "flips_of_100": flips,
            "flip_rate": flips / 100,
            "wilson_95_interval": wilson(flips, 100),
        }

    classification_counts = Counter(item["category"] for item in classifications)
    categories = ("brittle test assumption", "genuine firmware race/bug", "simulator/peripheral-model artifact", "unknown")
    summary = {
        "design": "100 prespecified seeds, each mapped to a uniform integer HSI frequency in [15.84, 16.16] MHz; nominal schedule fixed at 16 MHz",
        "legal_bound": {
            "clock": "STM32F407 HSI at 25 C",
            "frequency_hz_min": 15_840_000,
            "frequency_hz_nominal": 16_000_000,
            "frequency_hz_max": 16_160_000,
            "datasheet": "https://www.st.com/resource/en/datasheet/stm32f407ig.pdf",
            "datasheet_location": "DS8626 Rev 12, Section 3.12 and Table 34",
            "systick_manual": "https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf",
            "systick_manual_location": "PM0214 Rev 10, STK_CTRL.CLKSOURCE=1 selects processor/AHB clock",
        },
        "firmware_sha256": next(iter(firmware_hashes)),
        "test_sha256": {name: next(iter(values)) for name, values in test_hashes.items()},
        "simulator_version": next(iter(simulator_versions)),
        "rates": rates,
        "classification_counts": {category: classification_counts[category] for category in categories},
        "replayed_failures": sum(1 for item in replays.values() if item["identical_trace_and_verdict"]),
    }
    (RESULTS / "classifications.json").write_text(json.dumps(classifications, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
