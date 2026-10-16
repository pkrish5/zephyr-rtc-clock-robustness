#!/usr/bin/env python3
"""Read-only RTC mutant, source-style, and latency cross-tab audit."""

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/rtc_quality_cross_tabs.json"
LEDGER = ROOT / "analysis/rtc_quality_mutant_scores/rows.csv"
Z = 1.959963984540054
OPS = ("early", "late", "nonarrival")


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def wilson(k, n):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + Z * Z / n
    center = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [round(max(0, center - half), 6), round(min(1, center + half), 6)]


def rate(items, operator):
    planned = len(items)
    evaluable = [x[operator] for x in items if x[operator]["kill"] in ("yes", "no")]
    kills = sum(x["kill"] == "yes" for x in evaluable)
    return {"kills": kills, "evaluable": len(evaluable), "planned": planned,
            "missing": planned - len(evaluable), "rate": round(kills / len(evaluable), 6)
            if evaluable else None, "wilson95": wilson(kills, len(evaluable))}


def make_panel(grouped, with_both=False):
    rows = []
    for key, items in sorted(grouped.items()):
        result = {"group": list(key), "suites": len(items),
                  "mutants": {op: rate(items, op) for op in OPS}}
        if with_both:
            both_items = [x for x in items if all(x[op]["kill"] in ("yes", "no")
                                                  for op in ("early", "late"))]
            both = sum(x["early"]["kill"] == "yes" and x["late"]["kill"] == "yes"
                       for x in both_items)
            result["both_early_late"] = {"kills": both,
                                         "evaluable": len(both_items),
                                         "planned": len(items),
                                         "rate": round(both / len(both_items), 6)
                                         if both_items else None,
                                         "wilson95": wilson(both, len(both_items))}
        rows.append(result)
    return rows


def main():
    ledger = read_csv(LEDGER)
    waits = {x["suite_id"]: x for x in read_csv(ROOT / "analysis/rtc_static_waits.csv")}
    padding = {x["suite_id"]: x for x in read_csv(ROOT / "analysis/rtc_padding_audit.csv")}
    latency = {x["run_id"]: x for x in read_csv(ROOT / "analysis/factorial_latency_assumptions.csv")}
    distribution = json.loads((ROOT / "analysis/rtc_factorial_v2_final_summary.json").read_text())[
        "suite_distribution"]
    suites = defaultdict(dict)
    for row in ledger:
        sid, op = row["suite_id"], row["operator"]
        if op in suites[sid]:
            raise RuntimeError(f"Duplicate mutant row: {sid} {op}")
        suites[sid][op] = row
    if len(suites) != 69 or len(ledger) != 207:
        raise RuntimeError("Expected 69 suites and 207 mutant records")
    for sid, rows in suites.items():
        if set(rows) != set(OPS) or sid not in waits:
            raise RuntimeError(f"Incomplete mutant or wait-style rows: {sid}")
        if rows["early"]["kind"] == "ai" and sid not in padding:
            raise RuntimeError(f"Missing padding row: {sid}")

    cohort, wait_style, pad = defaultdict(list), defaultdict(list), defaultdict(list)
    for sid, rows in suites.items():
        row = rows["early"]
        key = (row["model"], row["prompt_condition"] or "none")
        cohort[key].append(rows)
        wait = waits[sid]
        style = ("fixed+event" if wait["fixed_sleep"] == "True" and
                 wait["event_wait"] == "True" else
                 "fixed_only" if wait["fixed_sleep"] == "True" else
                 "event_only" if wait["event_wait"] == "True" else "neither")
        wait_style[key + (style,)].append(rows)
        category = padding[sid]["over_padded"] if sid in padding else "not_coded"
        pad[key + (category,)].append(rows)

    zero_measured = {x["suite_id"]: x for x in distribution
                     if x["status"] == "measured" and x["model"] != "human" and x["fail"] == 0}
    if len(zero_measured) != 47:
        raise RuntimeError("Expected 47 measured AI suites with zero clock failures")
    latency_counts = Counter()
    for sid, x in zero_measured.items():
        source = latency[sid]
        if source["prompt_condition"] != x["prompt_condition"]:
            raise RuntimeError(f"Latency prompt mismatch: {sid}")
        category = source["latency_category"]
        if category == "latency_assumption_not_exposed_by_clock_rate":
            category = "definite"
        latency_counts[(x["model"], x["prompt_condition"], category)] += 1
    if sum(n for (_, _, cat), n in latency_counts.items() if cat == "definite") != 21:
        raise RuntimeError("Definite latency total changed")
    if sum(n for (_, _, cat), n in latency_counts.items() if cat == "unknown") != 23:
        raise RuntimeError("Unknown latency total changed")

    pooled_ai = [rows for sid, rows in suites.items() if rows["early"]["kind"] == "ai"]
    result = {"definition": "Wilson 95% intervals describe suite shares within the selected cohort; suites cluster by task and mutants are purposive, not random fault samples.",
              "mutant_by_model_prompt": make_panel(cohort, with_both=True),
              "mutant_all_ai": make_panel({("all_ai", "all_conditions"): pooled_ai},
                                          with_both=True)[0],
              "mutant_by_model_prompt_wait_style": make_panel(wait_style),
              "mutant_by_model_prompt_padding": make_panel(pad),
              "zero_clock_fail_latency_by_model_prompt":
              [{"model": model, "prompt_condition": prompt,
                "definite": latency_counts[(model, prompt, "definite")],
                "unknown": latency_counts[(model, prompt, "unknown")],
                "not_found": latency_counts[(model, prompt, "not_found")]}
               for model, prompt in sorted({(a, b) for a, b, _ in latency_counts})]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Audited 69 suites, 207 mutant records, and 47 zero-clock-failure AI sources")


if __name__ == "__main__":
    main()
