#!/usr/bin/env python3
"""Descriptive, post-start subcoding of frozen RTC not-predictable reasons."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORECAST = ROOT / "analysis/rtc_threshold_sample_v1/forecast.json"
OUT = ROOT / "analysis/rtc_threshold_sample_v2/not_predictable_categories.csv"
SUMMARY = ROOT / "notes/RTC_FACTORIAL_V2_REASON_CATEGORIES.md"
MULTI_STAGE = {
    "astra-range_present-rtc_alarm_pending-r05": ("CALENDAR_BUDGET_MS", "DELIVERY_BUDGET_MS"),
    "sol-range_present-rtc_alarm_pending-r05": ("deadline = k_uptime_get() + 30000", "deadline = k_uptime_get() + 30000"),
}
CATEGORIES = ("delivery_latency_or_order", "pending_polling_or_service_latency", "multi_stage_control_flow")


def main():
    source = json.loads(FORECAST.read_text())
    rows = []
    for p in sorted(source["predictions"], key=lambda x: x["run_id"]):
        if p["prediction_status"] != "not_predictable":
            continue
        text = (ROOT / p["source_path"]).read_text()
        if hashlib.sha256((ROOT / p["source_path"]).read_bytes()).hexdigest() != p["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {p['run_id']}")
        if p["task_family"] == "rtc_alarm_callback":
            category = "delivery_latency_or_order"
            evidence = "Frozen forecast cites IRQ delivery, callback service, or cross-context order."
        elif p["run_id"] in MULTI_STAGE:
            category = "multi_stage_control_flow"
            if p["run_id"].startswith("astra"):
                assert all(token in text for token in MULTI_STAGE[p["run_id"]])
                evidence = "Separate calendar and pending-delivery budgets in source."
            else:
                assert text.count(MULTI_STAGE[p["run_id"]][0]) == 2
                evidence = "Two distinct calendar and pending-delivery deadline loops in source."
        elif p["task_family"] == "rtc_alarm_pending":
            category = "pending_polling_or_service_latency"
            evidence = "Frozen forecast cites pending-state polling or peripheral service; no separate calendar/delivery budget coded."
        else:
            raise RuntimeError(f"Unexpected not-predictable family: {p['run_id']}")
        rows.append({"run_id": p["run_id"], "model": p["model"], "prompt_condition": p["condition"],
                     "task_family": p["task_family"], "category": category, "category_evidence": evidence,
                     "frozen_reason": p["prediction_reason"], "source_sha256": p["source_sha256"],
                     "coding_status": "descriptive_subcoding_after_execution_started"})
    if len(rows) != 36 or Counter(r["category"] for r in rows) != Counter({"delivery_latency_or_order": 19, "pending_polling_or_service_latency": 15, "multi_stage_control_flow": 2}):
        raise RuntimeError("Category audit did not cover frozen 36 not-predictable suites")
    with OUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    groups = Counter((r["model"], r["prompt_condition"], r["category"]) for r in rows)
    eligible = Counter((p["model"], p["condition"]) for p in source["predictions"])
    lines = ["# RTC v2 not-predictable reason categories", "",
             "Dated 2026-10-04. This is a **descriptive subcoding after varied execution began**. It does not change the frozen 66-suite forecast, 36 not-predictable decisions, sample, or outcome eligibility. The original reasons and frozen source hashes remain in the [row ledger](../analysis/rtc_threshold_sample_v2/not_predictable_categories.csv).", "",
             "The categories identify the primary reason clock rate alone cannot predict a verdict. They are mutually exclusive but do not inventory every timing assumption in a suite: callback delivery/order covers IRQ delivery, callback service, and cross-context ordering; pending polling/service covers a pending-bit observation window whose verdict can depend on polling or peripheral service; multi-stage control flow requires distinct calendar and pending-delivery budgets or loops in the frozen source. The last two cases are Astra present r05 and Sol present r05. These labels are not measured failure causes.", "",
             "| Model | Prompt | Eligible RTC suites | Callback delivery/order | Pending polling/service | Multi-stage control flow | Not predictable total |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for model in ("luna", "sol", "astra"):
        for condition in ("range_absent", "range_present"):
            counts = [groups[(model, condition, category)] for category in CATEGORIES]
            lines.append(f"| {model.title()} | {'Range present' if condition == 'range_present' else 'Range absent'} | {eligible[(model, condition)]} | {counts[0]} | {counts[1]} | {counts[2]} | {sum(counts)} |")
    lines += ["", "The range-present sources contain two explicit multi-stage pending tests versus zero in range-absent sources; Sol's not-predictable count is 10 versus 8 and Astra's is 9 in both conditions. These are small, eligibility-filtered cells and this finer category review was added after early outcomes were visible, so the differences are descriptive only. Luna's eligible RTC suites are counting tests, leaving no callback or pending comparison within Luna.", ""]
    SUMMARY.write_text("\n".join(lines))
    print(f"Wrote {len(rows)} rows to {OUT}; summary {SUMMARY}")


if __name__ == "__main__":
    main()
