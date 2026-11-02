# S2 reference validation results, 2026-11-02

Reference job **3547096 completed 0:0 in 39:00**, development / TRA25006,
one node; its reservation ceiling was 2 SUs. Scheduler start/end were
2026-11-02T11:15:22 / 11:54:22. No reference rerun or source change was needed.

The archive SHA-256 is
`7b4ce8ae94d65ec889a5026e3846911d3fba7028329798de44247f4b67e92fb6`.
Independent local verification checked all **3,137 entries**, exact extracted
inventory, kept ELFs/build logs/configurations, raw verdict/trace/UART/monitor
hashes, truthful job/container provenance, and both **30,067-file protected
audits**, unchanged. The archive receipt is complete. The local comparator ran
no new experiment and replaced no primary record.

## Qualification and coverage

All eleven reference builds succeeded. The **77 qualification launches**
passed the registered gate: 179 reference case passes, three anticipated
minimum-endpoint seconds-rate-contract failures, no skips, missing outcomes,
or harness errors. All nominal checks and all non-rate endpoint checks passed.

All **274 evaluation launches** completed, linking a task-specific reference
outcome to every one of the **470 original failing case slots**. Their 629
reference case outcomes were 524 passes and 105 retained rate-contract
failures, with no skips, missing outcomes, or harness errors. Shared launches
are never counted as independent developer tests or added to primary totals.

## Updated attribution with reference outcomes

Each cell is **distinct original case names (original failing case slots)**.
The board configurations share source/driver/simulator and are not independent
subjects. F767 is explicitly an F4 configuration replica.

| Board role | (a) Single-boundary wait; reference pass | (b) Phase-dependent wait; reference pass | (c) Cascade; clean-state reference pass | (d) Rate contract reference fails, progress passes |
|---|---:|---:|---:|---:|
| F4 | 1 (27) | 3 (80) | 1 (44) | 1 (35) |
| F4 configuration replica (F767) | 1 (27) | 3 (80) | 1 (44) | 1 (35) |
| F746 | 1 (27) | 2 (36) | 0 (0) | 1 (35) |
| H753, narrower legal envelope | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

Thus **277 waiting-failure slots passed their references**: 81 in (a), 196 in
(b). The references explicitly checked premature behavior and bounded arrival
under the registered experimental clock ceilings. This strengthens the
source/replay-supported waiting explanation within this simulation; it does
not validate silicon behavior or directly observe the fractional phase.

All **88 cascade slots** passed the clean-state single-shot reference. The
original setup failures remain category (c); they are not an additional
independent waiting defect. A clean-state success is not an experiment that
isolates the original cleanup path's causality.

For **all 105 seconds-rate slots**, the retained 1200-ms one-to-two-tick rate
assertion **failed**, and the separate legal-clock progress reference **passed**.
These receive a **firmware/simulator investigation flag, not test brittleness**.
The source explicitly advertises a rate check; whether that contract should
include the full legal LSI envelope remains unresolved. A failing reference
does not by itself prove a firmware or simulator bug, and the progress pass
must not silently replace the original property. No other reference failed.

## Original RTC cases: full application versus isolated cases

Unchanged F4 primary/isolated results, over the same registered 100 sampled
frequencies; endpoints are additional, not included in these denominators:

| Original case | Full-application seeded failures | Earlier isolated seeded failures | Isolated-fail/full-pass settings | Reference outcome at every full-app failure |
|---|---:|---:|---:|---|
| Alarm pending (`test_alarm`) | 26/100 | 26/100 | 0 | pass |
| Alarm callback | 22/100 | 26/100 | 4 | pass |
| Calendar counting | 12/100 | 17/100 | 5 | pass |

Including endpoints, counts are 27/27, 23/27, and 13/18 (full/isolated).
There are no isolated-pass/full-fail differences. Counter basic and seconds
have no earlier isolated baseline. The Renode calendar-write phase explanation
is **supported but not directly measured**; references are functional controls,
not measurements of the original full-application phase. F767 remains a
configuration replica, not another independent isolated-case baseline.

The distribution-free source boundaries, observed failing/passing frequency
bands, per-board/application runnable/skipped counts, and exact changed
frequencies remain in
`notes/s2_attribution_2026-10-31/s2_report_20261102_v3/`. No raw outcome or
reported primary count changed during reference validation.

## Files and next step

- Updated per-failure attribution: `verified-3547096-v1/primary_failure_reference_links.csv`
  (470 rows with reference case names, statuses, record/trace hashes and flags).
- Verification and board totals:
  `verified-3547096-v1/reference_validation_summary.json`.
- Reference phase gates and all raw evidence:
  `verified-3547096-v1/output/audits/` and the returned job archive.
- Frozen source/plan/ceilings: `PROTOCOL.md` and `packet/`.

S2 reference validation is complete; source-supported phase and accuracy-contract
limits remain explicit. Next is the authorized compute-node E partial-record
audit, then a dated quota-interruption amendment and exact incomplete/not-started
retry roster before any resumption. Completed records, including finalized
harness-error missing verdicts, remain unchanged and are not retried. E2 and
paper edits remain held; stop at Phase 3 before editing paper numbers.
