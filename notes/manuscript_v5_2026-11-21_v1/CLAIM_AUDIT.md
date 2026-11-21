# Manuscript v5 claim audit (2026-11-21)

`verify_manuscript_v5.py` (run by `make course-tables`) checks the current
`paper/draft/main.tex` against committed evidence without running firmware or
Renode. Status: **PASS, 52 numeric claims**. Outputs:
`claim_to_evidence_v5.csv` (claim, value, manuscript phrases, source files) and
`manuscript_numbers_v5.json` (the same with source SHA256s and the manuscript hash).

## What changed from v4

- Derived from `notes/course_improvement_2026-11-12_v1/verify_manuscript_v4.py`.
  Every v4 numeric check is retained against the same sources; only the
  manuscript phrases were updated to v5 wording.
- Four v4 claims are no longer stated in the v5 text (full/isolated failure
  counts, HSI evaluable runs, HSI interval detail, board survey). Their numbers
  are still checked against evidence and labelled "artifact only in v5". Other
  trimmed phrases (29 finalized missing outcomes, source lines 126--129/140--141,
  prompt-contrast statistics) are no longer required in the text but their
  numbers are still asserted.
- Table provenance: `subjects_review_v5.tex` must equal the audited
  `subjects_course_v2.tex` with the three generated-pending labels anonymized;
  `repairs_review_v6.tex` must equal the audited `repairs_course_v2.tex` with the
  constant 11.0-s median column dropped. `counter_sweep_v1.tex` is rebuilt by
  `notes/counter_natural_recovery_2026-11-20_v1/build_sweep_table.py`.
- The callback source excerpt is read from the committed
  `subjects/upstream_rtc_snapshot/` copy (byte-identical to the pinned checkout),
  so the audit runs in a fresh clone.
- Bibliography now has 17 keys, all cited.

## New v5 claims checked

| Claim | Source |
|---|---|
| 35 nominal passes; 98 primary 38 pass / 60 fail, 0 missing; 7 replays agree | `report-3598828-v1/summary.json` |
| 38/38 predicted rejects fail, 38/38 predicted accepts pass, 22/22 phase-dependent fail | `primary_cells.csv`, `PREDICTIONS.json` |
| Slow rates accepted per wait: 0, 1, 3, 3, 4, 6, 8 of 12 | `summary.json` |
| Lengthened-wait transitions imply > 2.6–2.9 ideal ticks; original 3-s bracket spans its whole band | `summary.json` |
| Right-sizing accepts 13, 14 and 16 kHz | `primary_cells.csv` |
| Original fails 17 kHz; all lengthened waits pass 17/32 kHz; at 10 kHz 13 s accepts, 7.648 s fixed/poll reject | `summary.json`, `primary_cells.csv` |
| Full-application case slots 147 pass / 185 fail / 746 skip | `summary.json` |
| 6-s wait margin 0.35 s over ideal 17-kHz three-tick arrival | arithmetic, 6 − 3·32000/17000 |
| Qualification 3589708: 84 processes, failed, 9 of 42 timing arrivals outside unchanged tolerance, all late by 0.08–0.29 s | `timing_diagnosis_3589708_v1.json`, `verified-3589708-v1/qualification.json` |
| Metadata attempt 3596807: not qualified, all 140 outcomes missing | `verified-3596807-v1/assessment.json` |

## Not covered

The audit checks numbers and their presence in the text, not interpretation.
Statements that phase was not measured, that the brackets are likely optimistic
for other phases, and that the 6-s wait is not a validated repair are author
judgments recorded in `report-3598828-v1/REPORT.md`.
