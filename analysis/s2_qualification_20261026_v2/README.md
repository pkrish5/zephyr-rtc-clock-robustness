# Verified S2 qualification re-analysis, 2026-10-26

Read `REPORT.md` first. Qualification is incomplete; no production is authorized.

Input: `results/s2_qualification_20261025_v1/evidence_v1.tar.gz`, containing the
frozen snapshot of 139 finalized records and incomplete-launch logs. No original
record was changed. Source annotations use the plan's upstream input hashes.

- `configuration_summary.csv`: board/application gates, runtime, memory, divider.
- `per_case_qualification.csv`: original sealed reporter's case-level output.
- `unfinished_calibration.csv`: six interrupted and nine unstarted settings.
- `omitted_after_nominal_gate.json`: 28 deliberately unattempted calibrations.
- `production_cost_scenarios.json`: conditional primary-only workload/SU estimates.
- `preliminary_failure_explanations.csv`, `source_excerpts.md`: six observed
  failing case names with source evidence; cascade and phase uncertainty retained.
- `verification.json`: independent file verification and no-experiment statement.

Reproduce into a fresh directory after extracting the archive:

```sh
python3 harness/tacc_s2_evidence/summarize.py \
  --evidence /path/to/extracted/evidence_v1 --out /path/to/new-analysis
python3 harness/tacc_s2_evidence/source_notes.py \
  --plan results/s2_qualification_20261025_v1/plan.json \
  --zephyr subjects/upstream/zephyr --out /path/to/new-analysis
```

The adjacent local v1 was an incomplete summary preparation stopped by an
optional CSV-header bug. It is not the result of a different experimental run.
