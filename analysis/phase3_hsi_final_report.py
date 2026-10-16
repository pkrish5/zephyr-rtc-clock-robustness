#!/usr/bin/env python3
"""Build the HSI report only when all registered runs and flip decisions exist."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/phase3_hsi_100mips"
RESULTS = BASE / "qualified"
SUMMARY = RESULTS / "summary.json"
CLASSIFICATIONS = ROOT / "analysis/phase3_hsi_classification_decisions.json"
LABELS = ("brittle_test_assumption", "firmware_race_or_bug",
          "simulator_or_peripheral_artifact", "unknown")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    summary = json.loads(SUMMARY.read_text())
    if not summary["complete"]:
        raise ValueError("HSI registered schedules are not complete")
    plan = json.loads((ROOT / "subjects/phase3_hsi_100mips/plan.json").read_text())
    candidates = plan["inventory"]
    if summary["candidate_versions"] != 44 or len(summary["versions"]) != 44:
        raise ValueError("Candidate inventory mismatch")
    expected_records = 44 * 5 + sum(row["nominal_5_of_5"] for row in summary["versions"].values()) * 102
    if summary["raw_record_count"] != expected_records:
        raise ValueError("Registered HSI record count incomplete")
    incident = json.loads((BASE / "execution_incident.json").read_text())
    if (incident["colliding_run_id"] != "upstream--context-seeded-027"
            or sha(ROOT / incident["tail_record_path"]) != incident["tail_record_sha256"]
            or "Refusing to overwrite raw output: upstream--context-seeded-027" not in
            (ROOT / incident["serial_log_path"]).read_text()):
        raise ValueError("Serial dispatcher incident evidence changed")
    raw_fails = {p.stem for p in (RESULTS / "records").glob("*.json")
                 if (lambda row: row["outcome"] == "fail" and row["condition"] in
                     ("seeded", "min", "max"))(json.loads(p.read_text()))}
    if not CLASSIFICATIONS.exists():
        if raw_fails:
            raise ValueError("Missing four-way flip decisions")
        CLASSIFICATIONS.write_text(json.dumps({"decisions": {}}, indent=2) + "\n")
    decisions = json.loads(CLASSIFICATIONS.read_text())["decisions"]
    if set(decisions) != raw_fails:
        raise ValueError("Four-way ledger does not cover exactly the observed flips")
    for run_id, row in decisions.items():
        if row["classification"] not in LABELS:
            raise ValueError(f"Unclassified flip: {run_id}")
        replay = json.loads((BASE / "replay_records" / f"{run_id}.json").read_text())
        if replay["run_id"] != run_id or row["replay_identical"] != replay["identical_trace_and_verdict"]:
            raise ValueError(f"Replay ledger mismatch: {run_id}")
    errors = []
    error_by_version = Counter()
    seeded_error_mips = Counter()
    unrelated = Counter()
    for path in (RESULTS / "records").glob("*.json"):
        row = json.loads(path.read_text())
        if row["outcome"] in ("harness_error", "timeout", "unknown", "skip"):
            errors.append((row["run_id"], row["outcome"]))
            error_by_version[(row["version_id"], row["condition"], row["outcome"])] += 1
            if row["condition"] == "seeded":
                seeded_error_mips[(row["kind"], row["cpu_performance_mips"])] += 1
        if row["kind"] == "upstream" and row["condition"] == "seeded":
            unrelated[(row["task_id"], "fail")] += sum(
                c["status"] == "fail" and c["case"] != row["selected_case"] for c in row["cases"])
    eligible_agents = [ident for ident, row in summary["versions"].items()
                       if candidates[ident]["kind"] == "agent" and row["nominal_5_of_5"]]
    eligible_humans = [ident for ident, row in summary["versions"].items()
                       if candidates[ident]["kind"] == "upstream" and row["nominal_5_of_5"]]
    seeded_agent_fails = sum(summary["versions"][ident]["failures"] for ident in eligible_agents)
    seeded_agent_evaluable = sum(summary["versions"][ident]["evaluable"] for ident in eligible_agents)
    seeded_human_fails = sum(summary["versions"][ident]["failures"] for ident in eligible_humans)
    seeded_human_evaluable = sum(summary["versions"][ident]["evaluable"] for ident in eligible_humans)
    mips_counts = ", ".join(f"{state} MIPS: {count} seeds" for state, count in
                             sorted(summary["schedule_mips_counts"].items(), key=lambda item: int(item[0])))
    diagnostic_outcomes = Counter()
    diagnostic_metadata = json.loads((BASE / "diagnostic_execution_metadata.json").read_text())
    if sha(ROOT / diagnostic_metadata["script_path"]) != diagnostic_metadata["script_sha256"]:
        raise ValueError("HSI diagnostic script changed")
    diagnostic_index = json.loads((BASE / "diagnostic_summary.json").read_text())["diagnostics"]
    original_error_ids = {run_id for run_id, outcome in errors if outcome == "harness_error"}
    if set(diagnostic_index) != original_error_ids:
        raise ValueError("Diagnostic index does not cover original harness errors")
    for run_id, outcome in errors:
        if outcome != "harness_error":
            continue
        path = BASE / "diagnostic_records" / f"{run_id}.json"
        if not path.exists():
            raise ValueError(f"Missing diagnostic for harness error: {run_id}")
        row = json.loads(path.read_text())
        if (row != diagnostic_index[run_id] or row["run_id"] != run_id
                or row["original_outcome"] != "harness_error"
                or sha(ROOT / row["original_record_path"]) != row["original_record_sha256"]
                or sha(ROOT / row["diagnostic_record_path"]) != row["diagnostic_record_sha256"]
                or json.loads((ROOT / row["diagnostic_record_path"]).read_text())["outcome"] !=
                row["diagnostic_outcome"]):
            raise ValueError(f"Diagnostic ledger mismatch: {run_id}")
        diagnostic_outcomes[row["diagnostic_outcome"]] += 1
    lines = [
        "# Phase 3 registered 100-MIPS HSI result — " + datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
        "",
        "The [frozen plan](../subjects/phase3_hsi_100mips/plan.json) covers ten upstream selected cases and 34 source-eligible Luna suites on the pinned STM32F407/Renode setup. Each version received five fresh nominal launches; only 5/5 passes entered the same 100 seeded HSI inputs and two exact endpoints. All surviving ELF and source hashes, simulator settings, platforms, UART/monitor logs, and sampled traces passed the [raw audit](../analysis/phase3_hsi_summary.py). The one earlier sandboxed Renode launch failed before virtual time advanced and remains a separate infrastructure record outside the fresh qualification screen. The serial dispatcher later stopped at an overwrite guard when it reached an active tail-shard run; the tail worker completed that run and the audit found no duplicate record or orphan artifact. The [incident record](../results/phase3_hsi_100mips/execution_incident.json), [execution partition metadata](../results/phase3_hsi_100mips/orchestration.json), and dated amendments preserve the host-concurrency changes.",
        "",
        f"The seeded frequency-to-CPU mapping produced {mips_counts}. Maximum absolute rounding error relative to the ideal `100 × f / 16 MHz` is {summary['max_quantization_error_mips']:.3f} MIPS. The [STM32F407 datasheet](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) supplies the HSI ±1% bound at 25 °C; the [direct Renode probe](../results/phase3_hsi_probe/fractional_mips_probe.json) and [time-model documentation](https://renode.readthedocs.io/en/latest/advanced/time_framework.html) motivate the integer-MIPS approximation. This is a documented oscillator-input range and an approximate CPU-throughput model, not a proved silicon execution schedule.",
        "",
        f"**Evaluable seeded verdicts:** upstream selected cases {seeded_human_fails}/{seeded_human_evaluable} fails across {len(eligible_humans)} nominally eligible cases; Luna {seeded_agent_fails}/{seeded_agent_evaluable} across {len(eligible_agents)} nominally eligible suites. These pooled counts are descriptive only: suites share ten tasks and every suite shares the same 100 inputs. The per-version and task tables below are the comparison units. Non-evaluable outcomes remain listed separately.",
        "",
        "## Task-stratified overview",
        "",
        "| Task | Upstream selected case, failures/evaluable | Luna nominally eligible / candidates | Luna failures/evaluable (descriptive) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for task_id, row in sorted(summary["task_summary"].items()):
        upstream = row["upstream"]
        human_rate = (f"{upstream['failures']}/{upstream['evaluable']}" if upstream else "none")
        agent_count = (f"{len(row['eligible_agent_versions'])}/{len(row['agent_versions'])}"
                       if row["agent_versions"] else "—")
        agent_rate = (f"{row['agent_failures']}/{row['agent_evaluable']}"
                      if row["agent_versions"] else "—")
        lines.append(f"| {task_id} | {human_rate} | "
                     f"{agent_count} | {agent_rate} |")
    lines.extend([
        "",
        "## Same-seed paired comparison by task",
        "",
        "Each eligible Luna suite is paired with its task's upstream selected case on the same saved seeds. Cells below sum version-level pairs within a task for readability; repeated upstream verdicts and shared seeds mean these are correlated counts, not independent trials. The version-specific cells are in the summary JSON.",
        "",
        "| Task | Evaluable pairs | Both pass | Both fail | Upstream only fails | Luna only fails |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for task_id in sorted(summary["task_summary"]):
        pairs = [p for p in summary["paired"] if p["task_id"] == task_id]
        cells = (" | ".join(str(sum(p[key] for p in pairs))
                            for key in ("evaluable_paired_seeds", "both_pass", "both_fail",
                                        "upstream_only_fail", "agent_only_fail"))
                 if pairs else "— | — | — | — | —")
        lines.append(f"| {task_id} | {cells} |")
    lines.extend([
        "",
        "## Per-version registered outcomes",
        "",
        "A flip rate is failures divided by evaluable seeded pass/fail verdicts, with a 95% Wilson interval. Endpoint challenges are outside that denominator. `—` means a version failed the fresh nominal screen and was not varied.",
        "",
        "| Task | Version | Nominal pass | Seeded pass | Seeded fail | Other/missing | Flip rate (95% Wilson) | Low endpoint | High endpoint |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ])
    for ident, row in summary["versions"].items():
        statuses = row["seeded_statuses"]
        ci = row["wilson_95"]
        rate = (f"{100 * row['flip_rate']:.1f}% ({100 * ci[0]:.1f}–{100 * ci[1]:.1f}%)"
                if ci else "—")
        other = sum(n for kind, n in statuses.items() if kind not in ("pass", "fail", "missing"))
        lines.append(f"| {row['task_id']} | {ident} | {row['nominal_statuses'].get('pass', 0)}/5 | "
                     f"{statuses.get('pass', 0)} | {statuses.get('fail', 0)} | "
                     f"{other} / {statuses.get('missing', 0)} | {rate} | "
                     f"{row['endpoints']['min']} | {row['endpoints']['max']} |")
    lines.extend([
        "",
        "The [100-row paired schedule table](../results/phase3_hsi_100mips/qualified/paired_schedules.csv) keeps all registered inputs, including missing or non-evaluable outcomes. The [summary JSON](../results/phase3_hsi_100mips/qualified/summary.json) contains each task-matched upstream/Luna pass/fail cell. The original strict source gate and amended functional gate select the same 34 HSI Luna candidates before fresh screening; their difference is material in the separate RTC callback arm, not in this HSI inventory. Upstream full-application logs also contain " + str(sum(unrelated.values())) + " failing unrelated case verdicts across seeded runs; these are reported separately from selected-case outcomes.",
        "",
        "## Replay and classification",
        "",
        f"{len(raw_fails)} seeded or endpoint test failures were captured. The [four-way decision ledger](../analysis/phase3_hsi_classification_decisions.json) is empty because no assertion flip required replay or classification. Counts: " + ", ".join(
            f"{label}={sum(row['classification'] == label for row in decisions.values())}"
            for label in LABELS) + ".",
        "",
        f"Non-evaluable qualified records: {len(errors)}. Fresh-process harness-error diagnostics: " +
        ", ".join(f"{status}={count}" for status, count in sorted(diagnostic_outcomes.items())) +
        ". Original outcomes remain unchanged. The [diagnostic index](../results/phase3_hsi_100mips/diagnostic_summary.json) preserves every run ID and diagnostic artifact.",
        "",
        "| Version | Condition | Non-evaluable outcome | Count |",
        "| --- | --- | --- | ---: |",
    ])
    for (ident, condition, outcome), count in sorted(error_by_version.items()):
        lines.append(f"| {ident} | {condition} | {outcome} | {count} |")
    lines.extend([
        "",
        "Seeded non-evaluable counts by model CPU setting: " + "; ".join(
            f"{kind}: " + ", ".join(f"{mips} MIPS={seeded_error_mips[(kind, mips)]}"
                                      for mips in (99, 100, 101))
            for kind in ("agent", "upstream")) + ". Their spread across settings does not establish that missing verdicts are random; rates remain conditional on evaluable runs.",
        "",
        "The HSI arm changes oscillator/SysTick rate with an integer CPU-throughput approximation. It does not independently vary ISR delivery delay, scheduling latency, peripheral response, or RTC LSI rate. The zero flip count is a negative result only for this frozen model and schedule set, conditional on the evaluable runs. Physical-board confirmation and independent source labels remain open. No Sol/Astra generation or repair is included.",
        "",
        "Reproduce the derived audit and report:",
        "",
        "```sh",
        "python3 analysis/phase3_hsi_plan.py",
        "python3 analysis/phase3_hsi_summary.py",
        "python3 analysis/phase3_hsi_final_report.py",
        "```",
        "",
    ])
    (ROOT / "notes/PHASE3_HSI_100MIPS_REPORT.md").write_text("\n".join(lines))
    print(f"Wrote final HSI report: {len(raw_fails)} test failures; {len(errors)} non-evaluable qualified records")


if __name__ == "__main__":
    main()
