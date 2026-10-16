#!/usr/bin/env python3
"""Write the final paired RTC report only after all registered work is audited."""

import json
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/phase3_rtc"
DECISIONS = ROOT / "analysis/phase3_rtc_classification_decisions.json"
VERSIONS = ("upstream", "luna_primary_r04", "rtc_bound_r05")
LABEL = {
    "upstream": "Repository-maintained selected case",
    "luna_primary_r04": "Luna primary r04",
    "rtc_bound_r05": "Luna bound-context supplement r05",
}


def main() -> None:
    summary = json.loads((RESULTS / "summary.json").read_text())
    if summary["raw_record_count"] != 321:
        raise ValueError("Expected 3 × (5 nominal + 100 seeded + 2 endpoints) raw runs")
    for ident in VERSIONS:
        row = summary["versions"][ident]
        if sum(row["seeded_statuses"].values()) != 100 or any(
                status == "missing" for status in row["endpoints"].values()):
            raise ValueError(f"Unfinished registered schedule: {ident}")
    decisions = json.loads(DECISIONS.read_text())["decisions"]
    raw_fails = {p.stem for p in (RESULTS / "records").glob("*.json")
                 if (lambda r: r["outcome"] == "fail" and r["condition"] in
                     ("seeded", "min", "max"))(json.loads(p.read_text()))}
    if set(decisions) != raw_fails:
        raise ValueError("Flip ledger does not match all seeded and endpoint failures")
    for run_id, row in decisions.items():
        if row["classification"] == "pending" or not row["replay_record_path"]:
            raise ValueError(f"Unclassified or unreplayed flip: {run_id}")
        replay = json.loads((ROOT / row["replay_record_path"]).read_text())
        if replay["run_id"] != run_id or replay["identical_trace_and_verdict"] != row["replay_identical"]:
            raise ValueError(f"Replay ledger mismatch: {run_id}")
    diagnostic_ids = ("luna_primary_r04-seeded-013", "upstream-seeded-056",
                      "upstream-seeded-062")
    for run_id in diagnostic_ids:
        original = json.loads((RESULTS / "records" / f"{run_id}.json").read_text())
        diagnostic = json.loads((RESULTS / "replay_records" / f"{run_id}.json").read_text())
        if (original["outcome"] != "harness_error" or diagnostic["outcome"] != "pass"
                or diagnostic["identical_trace_and_verdict"]):
            raise ValueError(f"Harness-error diagnostic unresolved: {run_id}")
    counts = {ident: Counter() for ident in VERSIONS}
    for row in decisions.values():
        counts[row["version_id"]][(row["condition"], row["classification"])] += 1

    plan = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())
    frequencies = plan["seeded_frequencies_hz"]
    if len(frequencies) != 100 or plan["lsi_bound_hz"] != [17000, 47000]:
        raise ValueError("RTC schedule or legal range differs from registered plan")
    # The supplement starts its 24-second first-callback timeout only after a
    # separate two-second pre-alarm sleep; both advance the RTC calendar.
    deadlines = {"upstream": 13, "luna_primary_r04": 15, "rtc_bound_r05": 26}
    source_windows = {"upstream": "3 s + 10 s", "luna_primary_r04": "15 s",
                      "rtc_bound_r05": "2 s + 24 s"}
    threshold_rows = []
    for ident in VERSIONS:
        deadline = deadlines[ident]
        boundary = Fraction(10 * 128 * 250, deadline)
        predicted = {seed for seed, hz in enumerate(frequencies) if hz < boundary}
        observed = set()
        non_evaluable = set()
        for seed in range(100):
            record = json.loads((RESULTS / "records" / f"{ident}-seeded-{seed:03d}.json").read_text())
            if record["lsi_frequency_hz"] != frequencies[seed]:
                raise ValueError(f"Frequency mismatch: {ident} seed {seed}")
            if record["outcome"] == "fail":
                observed.add(seed)
            elif record["outcome"] != "pass":
                non_evaluable.add(seed)
        discordant = sorted((predicted ^ observed) - non_evaluable)
        threshold_rows.append((ident, deadline, boundary, len(predicted), len(observed),
                               len(non_evaluable), discordant))

    lines = [
        "# Phase 3 selected RTC paired result — " + datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
        "",
        "All three registered 100-seed batches, five nominal repeats per version, and both endpoint challenges are complete. The raw audit checks the frozen source and ELF hashes, Renode version, CPU/SysTick/quantum, saved platform differences, seeds, and trace hashes. The same 100 distinct LSI input frequencies were used for each version. [STM32F407 DS8626 Rev. 12 Table 35](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) specifies 17–47 kHz at 3 V over −40 to 105 °C; board-level confirmation remains open.",
        "",
        "| Test version | Nominal | Seeded pass | Seeded fail | Non-evaluable | Flip rate, evaluable seeds (95% Wilson) | 17 kHz | 47 kHz | Original strict gate | Amended functional gate |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for ident in VERSIONS:
        row = summary["versions"][ident]
        statuses = row["seeded_statuses"]
        ci = row["wilson_95"]
        interval = (f"{row['pass_to_fail']}/{row['evaluable']} = {100*row['flip_rate']:.1f}% "
                    f"({100*ci[0]:.1f}–{100*ci[1]:.1f}%)" if ci else "undefined")
        non = ", ".join(f"{key} {count}" for key, count in statuses.items()
                        if key not in ("pass", "fail")) or "0"
        strict = "n/a" if row["original_strict_gate"] is None else ("yes" if row["original_strict_gate"] else "no")
        amended = "n/a" if row["amended_functional_gate"] is None else ("yes" if row["amended_functional_gate"] else "no")
        lines.append(f"| {LABEL[ident]} | {row['nominal_repeats'].get('pass', 0)}/5 | "
                     f"{statuses.get('pass', 0)} | {statuses.get('fail', 0)} | {non} | "
                     f"{interval} | {row['endpoints']['min']} | {row['endpoints']['max']} | "
                     f"{strict} | {amended} |")
    lines.extend([
        "",
        "The three original harness-error inputs (primary Luna seed 13, upstream seeds 56 and 62) each passed a separately saved fresh-process diagnostic. Their registered outcomes remain harness errors and do not enter evaluable flip denominators or paired pass/fail cells.",
        "",
        "The original strict source gate excludes both agent versions, so it yields **no eligible agent RTC comparison**. The dated split gate admits the primary Luna r04 as functionally adequate despite its 15-second timing bound. The bound-context r05 remains a separate prompt condition and its immediate second-callback `K_NO_WAIT` check remains timing-bound inadequate, despite 0/100 observed flips. The split was retrospective and unblinded to early RTC outcomes. No row shows a model-wide improvement estimate.",
        "",
        "## Prespecified clock-threshold check",
        "",
        "The programmed alarm is ten RTC calendar seconds after the starting time. With the selected STM32 prescalers (128 × 250 = 32,000 LSI ticks per calendar second), calendar arrival takes approximately `320,000 / f_LSI` real seconds. Equating that duration to each source deadline gives the boundary `f_LSI = 320,000 / deadline`. A lower input frequency predicts a deadline failure. This arithmetic predicts calendar/deadline failures only; setup, polling, and delivery can shift an exact boundary, so the saved run verdict is authoritative.",
        "",
        "| Test version | Source wait(s) | Calendar comparison window | Calendar failure boundary | Failing portion of legal 17–47 kHz range | Predicted failures among 100 seeds | Observed failures / evaluable seeds | Evaluable prediction disagreements |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ])
    for ident, deadline, boundary, predicted, observed, non_evaluable, discordant in threshold_rows:
        legal_range = (f"17,000 ≤ f < {float(boundary):,.1f} Hz" if boundary >= 17000
                       else "none (boundary below 17,000 Hz)")
        lines.append(f"| {LABEL[ident]} | {source_windows[ident]} | {deadline} s | "
                     f"{float(boundary):,.1f} Hz | "
                     f"{legal_range} | {predicted}/100 | {observed}/{100 - non_evaluable} | "
                     f"{len(discordant)} |")
    lines.extend([
        "",
        "The upstream 3 s plus 10 s fixed sleeps yield a 13 s arrival check and a 24,615.4 Hz boundary. Luna r04 asserts arrival within 15 s, yielding 21,333.3 Hz. The supplement first sleeps 2 s to check for a premature alarm, then waits up to 24 s for the first callback: its 26 s total calendar window yields a 12,307.7 Hz boundary, below the legal input range. These windows ignore setup time, which adds margin. Predictions match every evaluable saved seed: 26 upstream failures, 13 primary Luna failures, and zero supplement failures. The three harness-error seeds are retained as non-evaluable, so predicted counts use all 100 registered inputs while observed rates use 98, 99, and 100 evaluable runs. Endpoint behavior also agrees with the calendar calculation.",
        "",
        "LSI-frequency variation does not independently control interrupt delivery latency or the separation between the two callback deliveries. The supplement's immediate second `k_sem_take(..., K_NO_WAIT)` can therefore hide a delivery-latency assumption even when its main 24 s deadline covers the legal clock range. Its 0/100 calendar-clock flips do **not** establish full timing-bound adequacy.",
        "",
        "## Same-seed paired outcomes",
        "",
        "The complete [100-row paired table](../results/phase3_rtc/paired_schedules.csv) retains every registered seed and any harness error. Pairwise counts below use only seeds with pass/fail verdicts in both versions.",
        "",
        "| Pair (left / right) | Evaluable pairs | Both pass | Both fail | Left only fails | Right only fails |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for key, row in summary["pairwise"].items():
        left, right = key.split("__")
        lines.append(f"| {LABEL[left]} / {LABEL[right]} | "
                     f"{row['evaluable_paired_seeds']} | {row['both_pass']} | "
                     f"{row['both_fail']} | {row['left_only_fail']} | "
                     f"{row['right_only_fail']} |")
    lines.extend([
        "",
        "## Replay and four-way classification",
        "",
        "Every observed seeded or endpoint failure has an individual [classification record](../analysis/phase3_rtc_classification_decisions.json), frozen raw trace, and fresh-process replay. Endpoint failures are classified but are outside seeded-rate denominators. Counts by version and category:",
        "",
        "| Test version | Condition | Brittle test assumption | Firmware race/bug | Simulator/peripheral artifact | Unknown |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ])
    for ident in VERSIONS:
        for condition in ("seeded", "min", "max"):
            c = counts[ident]
            lines.append(f"| {LABEL[ident]} | {condition} | "
                         f"{c[(condition, 'brittle_test_assumption')]} | "
                         f"{c[(condition, 'firmware_race_or_bug')]} | "
                         f"{c[(condition, 'simulator_or_peripheral_artifact')]} | "
                         f"{c[(condition, 'unknown')]} |")
    lines.extend([
        "",
        "The decision procedure distinguishes a deadline assertion on otherwise allowed slow-clock behavior from firmware defects and Renode artifacts; divergent replay or insufficient evidence is retained as unknown. The STM32 peripheral model and the broad datasheet environmental range limit any physical-hardware claim. The two RTC state-observation additions are not part of this already locked three-version callback table.",
        "",
        "Reproduce the derived audit and report from the preserved raw records:",
        "",
        "```sh",
        "python3 analysis/phase3_rtc_summary.py",
        "python3 analysis/phase3_rtc_classify.py",
        "python3 analysis/phase3_rtc_final_report.py",
        "```",
        "",
    ])
    (ROOT / "notes/PHASE3_RTC_FINAL_REPORT.md").write_text("\n".join(lines))
    print(f"Final RTC report written: {len(raw_fails)} failures classified")


if __name__ == "__main__":
    main()
