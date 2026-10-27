# S2 completion check, 2026-10-27

Read-only `sacct` returned S2 primary job 3535524 as COMPLETED, exit 0:0,
elapsed 03:12:41, node c309-016. E replacement job 3535400 remained PENDING,
elapsed 00:00:00, no assigned node. This is a scheduler checkpoint, not an
audited case-level result or completed failure attribution.

The S2 scheduler logs were copied successfully into the new local directory
`artifacts/s2_production_20261026_v1/returned_20261027_v1/slurm/`.
The stdout contains exactly 1,122 distinct Launcher completion IDs, covering
1 through 1,122, and the stderr is empty. The final stdout message explicitly
requires outcome audit, replay and reference attribution.

The separate rsync of the completed bundle stalled before transferring any
records. Only that local transfer client was stopped (exit 20). No remote
job, source, result, or account setting was changed. Remote access is paused
under the user's connection rule until WORK/session responsiveness is
confirmed. The E output log does not exist yet because that job has not
started. No further job was submitted, and no experiment was rerun.

Before this check, all 30,067 protected files matched the baseline. Audit:
`artifacts/s2_production_20261026_v1/returned_20261027_v1/protected_before.json`,
SHA-256 e9eabf5c052519bc33125dc99b13a0195ac76e3668b467ad67528b72ae739cda.

Next: copy and independently verify the completed S2 raw records, including
their hashes, full expected task coverage, case-level passes/failures/skips,
and missing outcomes. Do not infer those counts from Slurm completion.
E2 and manuscript edits remain on hold. Existing manuscript changes were
left untouched.
