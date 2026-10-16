#!/usr/bin/env python3
"""Compute predeclared clock-window padding for the frozen RTC forecast ledger.

Only a single clock-only observation budget is comparable to the 10-second RTC
transition. A not-predictable source is retained as unknown, not called safe.
"""

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/rtc_threshold_sample_v1/forecast_table.csv"
OUT = ROOT / "analysis/rtc_padding_audit.csv"
SUMMARY = ROOT / "notes/RTC_STATIC_PADDING_AND_WAITS.md"
WORST_CASE_S = 10 * 32000 / 17000
OVER_PADDING_RATIO = 2.0


def main():
    rows = []
    with SOURCE.open(newline="") as f:
        for item in csv.DictReader(f):
            budget = float(item["budget_seconds"]) if item["budget_seconds"] else None
            ratio = budget / WORST_CASE_S if budget is not None else None
            row = {"suite_id": item["run_id"], "model": item["model"],
                   "prompt_condition": item["condition"], "task_family": item["task_family"],
                   "clock_only_budget_s": item["budget_seconds"],
                   "worst_legal_10_rtc_s": f"{WORST_CASE_S:.6f}",
                   "budget_source_expression": item["budget_source_expression"],
                   "padding_ratio": f"{ratio:.3f}" if ratio is not None else "",
                   "over_padded": ("yes" if ratio > OVER_PADDING_RATIO else "no")
                   if ratio is not None else "unknown",
                   "reason": item["prediction_reason"]}
            rows.append(row)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped = defaultdict(Counter)
    for row in rows:
        grouped[(row["model"], row["prompt_condition"])][row["over_padded"]] += 1
    lines = [
        "# Static RTC padding and wait inventory — 2026-10-05",
        "",
        "This is a source-only descriptive analysis. The frozen forecast ledger supplies",
        "a single clock-only observation budget for 30 of 66 functionally eligible RTC",
        "suites. The other 36 have no defensible scalar budget under LSI rate alone",
        "and remain `unknown` for this padding metric. The per-suite CSV retains",
        "every denominator member and source expression.",
        "",
        f"For a ten-calendar-second target, the slow legal LSI endpoint requires "
        f"`10 × 32000 / 17000 = {WORST_CASE_S:.6f}` host seconds in the ideal",
        "clock model. Define the descriptive padding ratio as source observation",
        "budget divided by this bound. A ratio strictly greater than 2 is coded",
        "`over_padded`. This threshold is an analysis convention, not a hardware",
        "upper limit or proof that a lower ratio is adequate. It excludes phase,",
        "polling, scheduling, and callback latency; source labels with no scalar",
        "budget are left unknown. Thus it cannot certify a timing oracle.",
        "",
        "| Model | Prompt | Over padded | At or below 2× | Unknown | Rate among assessable |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for (model, condition), counts in sorted(grouped.items()):
        yes, no, unknown = counts["yes"], counts["no"], counts["unknown"]
        rate = f"{yes}/{yes+no} ({yes/(yes+no):.1%})" if yes + no else "undefined"
        lines.append(f"| {model} | {condition} | {yes} | {no} | {unknown} | {rate} |")
    lines += ["", "The [wait-style ledger](../analysis/rtc_static_waits.csv) records",
              "source-pattern flags and the median of existing saved nominal pass",
              "wall times for each eligible AI suite, plus the separately",
              "qualified nominal logs for the three human selected cases. It",
              "makes no new simulation runs. A source may have multiple wait styles.", ""]
    waits = list(csv.DictReader((ROOT / "analysis/rtc_static_waits.csv").open()))
    lines += ["| Model | Prompt | Eligible suites | Fixed sleep syntax | Event-wait API syntax | Median of per-suite nominal medians (wall s) |",
              "|---|---|---:|---:|---:|---:|"]
    for (model, condition), _ in sorted(grouped.items()):
        cell = [row for row in waits if row["model"] == model and row["prompt_condition"] == condition]
        sleep = sum(row["fixed_sleep"] == "True" for row in cell)
        event = sum(row["event_wait"] == "True" for row in cell)
        runtime = statistics.median(float(row["nominal_wall_median_s"]) for row in cell)
        lines.append(f"| {model} | {condition} | {len(cell)} | {sleep} | {event} | {runtime:.2f} |")
    lines += ["", "These syntax flags can overlap. In particular, an event API",
              "called with `K_NO_WAIT` is counted as syntax, not as a genuine",
              "blocking wait. The per-suite CSV is the authoritative runtime",
              "inventory; a cell median does not replace it.", ""]
    SUMMARY.write_text("\n".join(lines))
    print(f"Wrote {len(rows)} padding rows and summary")


if __name__ == "__main__":
    main()
