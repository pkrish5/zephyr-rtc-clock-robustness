# Provisional S2 primary accounting, 2026-10-27

**Record metadata only. UART, monitor, trace and remote ELF bytes have not
yet been verified. This is not completed replay/reference attribution.**

Source: all 1,122 JSON records copied from completed LS6 job 3535524 into
`artifacts/s2_production_20261026_v1/returned_20261027_v1/bundle/`.
Every task index, frequency, condition, saved plan hash, image identity,
Renode version, module metadata, and declared case set matched the frozen
production plan. `record_sha256.json` records each copied record's digest.
Source plan: `results/s2_production_20261026_v1/plan.json` (identical SHA-256
719b3bc42f2b93f44455a11eca3eacd69eacbbf4e8c714b90300d5a8343d0612).
Nominal comparison: `analysis/s2_qualification_final_20261026_v1/per_case_cohort.csv`.

There are 1,122 records, no missing task indices, and all records report a
complete application with no error, missing case, or duplicate case. All
6,630 declared case slots have a reported status: 3,022 pass, 470 fail,
3,138 skip, zero missing. These counts remain provisional until log checks.
`process_exit_counts` is empty because wrapper process records have not been
copied; it does not mean their exit codes were independently checked.

`per_case.csv` separates the 100 sampled settings from each exact endpoint;
`primary_failures.csv` lists the 470 failure observations with source-record
hashes. `per_board.csv` preserves board replicas and nominal baselines.
F4 and F767 each have 6/10 nominally runnable cases with a recorded failure;
F746 has 4/6 and H753 0/9. Across all legal settings, H753 has 10 cases that
run at least once, rather than the nine nominally runnable cases: its
`test_short_relative_alarm` passes at 10 sampled settings and skips at the
other 90 and both endpoints. Do not recode skips as passes or silently use a
fixed per-frequency capability denominator.

Do not equate these failed cases with independent brittle timing defects.
In particular, the counter application's single-shot setup failure may be
a shared-state cascade after its all-channels failure. The seconds-rate
case asserts an intentional clock-rate contract. Source, replay and
reference evidence must resolve attribution; no new such runs were made.

Reproduce with `harness/tacc_s2_evidence/audit_primary.py --records-only`,
the copied record bundle, sealed production plan and nominal-case ledger.
Run without that flag into a fresh output directory after retrieving the
remaining evidence. E2 and manuscript edits remain held.
