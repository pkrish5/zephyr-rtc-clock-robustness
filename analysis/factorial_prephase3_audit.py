#!/usr/bin/env python3
"""Reconcile frozen factorial gates and export the pre-Phase-3 review tables."""

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "results/spec_context_factorial_v1/gate_summary.json"
SOURCE = ROOT / "analysis/factorial_source_decisions.json"
TASKS = ROOT / "subjects/phase2_tasks_v2.json"
OUT = ROOT / "analysis/factorial_prephase3"
FAMILIES = {
    "rtc_alarm_callback": "RTC callback",
    "rtc_time_counting": "RTC counting",
    "rtc_alarm_pending": "RTC pending",
}


def family(task_id, arms):
    return "HSI (10 tasks)" if arms[task_id] == "hsi" else FAMILIES[task_id]


def main():
    gate = json.loads(GATES.read_text())
    decisions = json.loads(SOURCE.read_text())["decisions"]
    arms = {task["id"]: task["arm"] for task in json.loads(TASKS.read_text())["tasks"]}
    rows = gate["rows"]
    assert len(rows) == len(decisions) == 390
    assert len({row["run_id"] for row in rows}) == 390
    for row in rows:
        decision = decisions[row["run_id"]]
        assert row["source_sha256"] == decision["source_sha256"]
        assert row["functional"] == decision["functional"]
        assert row["timing_bound"] == decision["timing_bound"]
        assert row["nominal_5of5_screened"] == all(
            value != "missing" for value in row["nominal_repeats"])
        expected_functional = (row["build"] == "pass" and
                               row["fresh_nominal_5of5"] and row["functional"] == "met")
        expected_strict = expected_functional and row["timing_bound"] == "no_issue_found"
        assert row["amended_functional_eligible"] == expected_functional
        assert row["original_strict_eligible"] == expected_strict

    by_cell = defaultdict(list)
    for row in rows:
        by_cell[(row["model"], row["condition"], family(row["task_id"], arms))].append(row)

    OUT.mkdir(parents=True, exist_ok=True)
    table_path = OUT / "model_condition_family.csv"
    columns = ["model", "prompt_condition", "task_family", "generated", "built",
               "first_nominal_pass", "nominal_5of5_pass", "source_functional_met",
               "functional_gate_eligible", "strict_gate_eligible",
               "timing_no_issue_found_all_source", "timing_inadequate_all_source",
               "timing_unknown_all_source", "timing_no_issue_found_eligible",
               "timing_inadequate_eligible", "timing_unknown_eligible"]
    summary = []
    for model in ("luna", "sol", "astra"):
        for condition in ("range_absent", "range_present"):
            for fam in ("HSI (10 tasks)", "RTC callback", "RTC counting", "RTC pending"):
                group = by_cell[(model, condition, fam)]
                count = lambda predicate: sum(bool(predicate(row)) for row in group)
                eligible = [row for row in group if row["amended_functional_eligible"]]
                item = {
                    "model": model, "prompt_condition": condition, "task_family": fam,
                    "generated": len(group), "built": count(lambda r: r["build"] == "pass"),
                    "first_nominal_pass": count(lambda r: r["first_nominal"] == "pass"),
                    "nominal_5of5_pass": count(lambda r: r["fresh_nominal_5of5"]),
                    "source_functional_met": count(lambda r: r["functional"] == "met"),
                    "functional_gate_eligible": len(eligible),
                    "strict_gate_eligible": count(lambda r: r["original_strict_eligible"]),
                }
                for label, key in (("no_issue_found", "no_issue_found"),
                                   ("inadequate", "inadequate"), ("unknown", "unknown")):
                    item[f"timing_{key}_all_source"] = count(lambda r: r["timing_bound"] == label)
                    item[f"timing_{key}_eligible"] = sum(r["timing_bound"] == label for r in eligible)
                assert sum(item[f"timing_{key}_eligible"] for key in
                           ("no_issue_found", "inadequate", "unknown")) == len(eligible)
                assert item["strict_gate_eligible"] == item["timing_no_issue_found_eligible"]
                summary.append(item)
    with table_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(summary)

    excluded = []
    for row in sorted(rows, key=lambda r: r["call_index"]):
        if row["functional"] == "met":
            continue
        if row["build"] != "pass":
            other_screen = "build failure; no nominal run"
        elif row["first_nominal"] == "pass":
            other_screen = "first nominal pass; repeats not run"
        elif row["first_nominal"] == "fail":
            other_screen = "first nominal assertion fail; repeats not run"
        else:
            other_screen = "first nominal timeout; repeats not run"
        decision = decisions[row["run_id"]]
        excluded.append({
            "call_index": row["call_index"], "run_id": row["run_id"],
            "model": row["model"], "prompt_condition": row["condition"],
            "task_family": family(row["task_id"], arms),
            "source_path": decision["source_path"],
            "build": row["build"], "first_nominal": row["first_nominal"],
            "nominal_repeats": "/".join(row["nominal_repeats"]),
            "other_screen_outcome": other_screen,
            "functional_filter": "excluded: not_met",
            "strict_filter": "excluded: functional not_met",
            "functional_evidence": decision["functional_evidence"],
        })
    assert len(excluded) == 60
    exclusion_path = OUT / "functional_inadequate_suites.csv"
    with exclusion_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(excluded[0]))
        writer.writeheader()
        writer.writerows(excluded)

    totals = Counter()
    for row in rows:
        totals["generated"] += 1
        totals["built"] += row["build"] == "pass"
        totals["nominal_5of5"] += row["fresh_nominal_5of5"]
        totals["nominal_5of5_screened"] += row["nominal_5of5_screened"]
        totals["source_functional_met"] += row["functional"] == "met"
        totals["source_functional_not_met"] += row["functional"] == "not_met"
        totals["functional_gate_eligible"] += row["amended_functional_eligible"]
        totals["strict_gate_eligible"] += row["original_strict_eligible"]
    assert totals == Counter({"generated": 390, "built": 360, "nominal_5of5": 321,
                              "nominal_5of5_screened": 330,
                              "source_functional_met": 330, "source_functional_not_met": 60,
                              "functional_gate_eligible": 321, "strict_gate_eligible": 175})

    def seed_records(directory):
        for path in directory.glob("*.json"):
            record = json.loads(path.read_text())
            if record.get("seed") is not None and record.get("outcome") != "harness_error":
                yield record

    hsi_history = defaultdict(list)
    for record in seed_records(ROOT / "results/phase3_hsi_100mips/qualified/records"):
        hsi_history[record["task_id"]].append(record["wall_seconds"])
    rtc_history = list(seed_records(ROOT / "results/phase3_rtc/records"))
    hsi_counts = Counter(row["task_id"] for row in rows
                         if row["amended_functional_eligible"] and arms[row["task_id"]] == "hsi")
    rtc_count = sum(row["amended_functional_eligible"] and arms[row["task_id"]] != "hsi"
                    for row in rows)
    hsi_seconds = sum(count * 102 * statistics.mean(hsi_history[task])
                      for task, count in hsi_counts.items())
    rtc_seconds = rtc_count * 102 * statistics.mean(record["wall_seconds"]
                                                    for record in rtc_history)

    def md(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    report = [
        "# Pre-Phase-3 factorial gate reconciliation — 2026-10-04 UTC",
        "",
        "**Status:** read-only audit of frozen sources, source decisions, and registered nominal records. No new timing schedule was run.",
        "",
        "## Why both final counts are 321",
        "",
        "The amended eligibility expression in `analysis/factorial_gate_summary.py` is "
        "`build pass AND nominal 5/5 AND functional == met`. The original strict "
        "expression adds `timing_bound == no_issue_found`. The audit recomputed both "
        "expressions independently for all 390 rows and found no mismatch.",
        "",
        "| Stage | Suites |",
        "|---|---:|",
        "| Generated | 390 |",
        "| Built | 360 |",
        "| Source functionally adequate (`met`), regardless of build/nominal | 330 |",
        "| Source functionally inadequate (`not_met`) | 60 |",
        "| First nominal pass | 336 |",
        "| Five registered nominal passes | 321 |",
        "| Build + 5/5 + functional `met` (amended primary) | 321 |",
        "| Build + 5/5 + functional `met` + timing `no_issue_found` (original strict) | 175 |",
        "",
        "The equality of 5/5 and amended-eligible counts follows from the screening "
        "order, not an omitted filter: only built suites labeled `functional=met` "
        "received all five nominal repeats. All 330 source-met suites built; 321/330 "
        "passed 5/5 and nine did not. Of the 60 source-not-met suites, 30 failed build. "
        "The other 30 received one nominal run: 12 passed, 17 failed an assertion, "
        "and one timed out. **No source-inadequate suite received a five-repeat "
        "screen, so its 5/5 outcome is unmeasured, not failed.** The functional "
        "filter rejects all 60. Among the 321 amended-eligible suites, 105 "
        "have `timing=inadequate`, 175 `no_issue_found`, and 41 `unknown`. Thus the "
        "strict gate excludes 146 additional runnable, functionally adequate suites.",
        "",
        "The source reviewer treats a weak assertion that would let a plausible "
        "violation pass (for example, accepting a 30 ms wake for a requested 40 ms "
        "sleep) as a functional-oracle problem. An otherwise meaningful assertion "
        "whose chosen deadline can falsely fail under a legal schedule is a timing-bound "
        "problem. The vacuous delayed-work case below is functionally inadequate "
        "because its lower-bound expression becomes `elapsed >= 0` at 8,000 ticks/s; "
        "it also failed to compile. No source or raw result was changed by this audit.",
        "",
        "## Model × prompt × task-family table",
        "",
        "`Nominal` means all five registered passes. `Source met` is the source-only "
        "functional label; `Functional gate` adds build and nominal 5/5. "
        "Timing `N/I/U` counts all generated sources as no issue found / inadequate / "
        "unknown; `no issue found` is not a proof of adequacy. The three RTC tasks "
        "remain separate because they are correlated cases, not independent subjects. "
        "The [CSV](../analysis/factorial_prephase3/model_condition_family.csv) also "
        "reports timing labels within the eligible set and first nominal passes.",
        "",
        "| Model | Range | Family | Generated | Built | Nominal | Source met | Functional gate | Strict gate | Timing N/I/U, all source |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        timing = "/".join(str(item[f"timing_{key}_all_source"]) for key in
                          ("no_issue_found", "inadequate", "unknown"))
        report.append("| " + " | ".join(map(str, (
            item["model"], item["prompt_condition"].removeprefix("range_"),
            item["task_family"], item["generated"], item["built"],
            item["nominal_5of5_pass"], item["source_functional_met"],
            item["functional_gate_eligible"], item["strict_gate_eligible"], timing))) + " |")
    report += [
        "",
        "## Every source-inadequate suite and its exclusion",
        "",
        "Each listed suite is rejected by the source functional filter and the original "
        "strict gate. `Other screen outcome` shows its build or single nominal result; "
        "none was advanced to a five-repeat screen. Full records and evidence are in "
        "the [exclusion CSV](../analysis/factorial_prephase3/functional_inadequate_suites.csv).",
        "",
        "| Call | Frozen suite | Other screen outcome | Functional evidence |",
        "|---:|---|---|---|",
    ]
    for item in excluded:
        link = f"[{md(item['run_id'])}](../{item['source_path']})"
        report.append(f"| {item['call_index']} | {link} | "
                      f"{md(item['other_screen_outcome'])} | "
                      f"{md(item['functional_evidence'])} |")
    report += [
        "",
        "## Estimated execution time after approval",
        "",
        "The primary schedule has 100 seeds plus two separately reported endpoint "
        "challenges per suite. This gives **66 RTC/LSI suites × 102 = 6,732 fresh "
        "processes** and **255 HSI suites × 102 = 26,010**. Counts exclude replays "
        "of assertion failures and any additional upstream baseline runs.",
        "",
        f"The prior selected RTC seeded arm has {len(rtc_history)} evaluable runs "
        f"with mean **{statistics.mean(r['wall_seconds'] for r in rtc_history):.2f} s** "
        f"per process. Applying that mean to the new RTC count gives **{rtc_seconds/3600:.1f} "
        "serial machine-hours**. This is a rough transfer from RTC callback suites; "
        "calendar-counting and alarm-pending code can have different horizons. "
        "A planning range of roughly **90–160 serial hours** is prudent.",
        "",
        f"The prior 100-MIPS HSI arm has {sum(map(len,hsi_history.values()))} evaluable "
        "seeded runs. Weighting each task's measured mean by its new eligible-suite "
        f"count gives **{hsi_seconds/3600:.1f} serial machine-hours** for 26,010 "
        "processes; use roughly **70–130 serial hours** for planning. The task-weighted "
        "figure is higher than an unweighted all-task average because the new suite "
        "mix contains more slow tasks.",
        "",
        "With three independent Renode workers and ideal scaling, the base scans "
        f"would take about **{rtc_seconds/3600/3:.0f} h RTC** and "
        f"**{hsi_seconds/3600/3:.0f} h HSI** of wall time. Host contention, startup "
        "errors, logging, and replay make actual elapsed time longer. Each failing "
        "schedule requires a fresh exact replay, so add roughly one extra run's "
        "duration per failure: about 60 s per RTC failure or a task-dependent HSI "
        "duration. If all runs failed, replay could approximately double the base "
        "cost; the failure count is unknown before variation. Existing matched upstream "
        "runs cover the ten HSI cases and RTC callback; the two selected RTC state "
        "baselines may require fresh 100-seed runs under their locked schedules.",
        "",
        "The preregistration fixes the inputs, eligible suite set, schedule order "
        "within each suite, and analyses, but does not require HSI to precede the new "
        "RTC arm. Running **RTC/LSI first** is compatible with it and surfaces the "
        "wide-tolerance signal sooner. Finish and preserve that arm before HSI; "
        "do not change either arm's eligibility, seeds, or endpoints in response "
        "to the first arm's outcomes. Start neither arm before user approval.",
        "",
    ]
    report_path = ROOT / "notes/PHASE3_PRESTART_GATE_RECONCILIATION.md"
    report_path.write_text("\n".join(report))
    print(dict(totals))
    print(f"Wrote {table_path.relative_to(ROOT)}, {exclusion_path.relative_to(ROOT)}, "
          f"and {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
