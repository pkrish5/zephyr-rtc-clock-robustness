# Counter-repair primary-evidence handoff, 2026-11-10

All three recovery archives and primary records passed independent verification. This is one upstream subject with three interventions, not 306 independent tests. Scientific interpretation still requires the original protocol's replay/reference and fault-control checks. The manuscript is unchanged.

|Group / job|Selected pass|Fail|Skip|Missing|Later single-shot pass / fail|
|---|---:|---:|---:|---:|---|
|legal-a / 3570473|153|0|0|0|131 / 22|
|legal-b / 3570474|153|0|0|0|130 / 23|
|fault / 3570475|5|3|0|0|4 / 4|

## Paired legal settings for the selected all-channels case

The archived V0 has 58 passes and 44 failures at 102 settings. Each V1, V1b and V2 has 102 selected-case passes at those same exact settings, with zero skip/missing. All 44 originally failing settings pass under each intervention. No V0 legal run was repeated.

|Variant|All-channels pass / fail|Short-relative pass / fail|Later single-shot pass / fail|
|---|---|---|---|
|V1|102 / 0|88 / 14|87 / 15|
|V1b|102 / 0|88 / 14|87 / 15|
|V2|102 / 0|88 / 14|87 / 15|

The full application is **not uniformly passing**. In each variant, 29 of the original 44 later single-shot failures become passes and 15 remain failures. The short-relative case, formerly skipped at those 44 baseline settings, now passes 30 and fails 14. Every originally passing setting remains passing for these cases. These are observations; the cause of each remaining failure and whether it is a cleanup cascade require replay/reference and source attribution. Recorded skips stay skips and are not imputed as passes.

Full case-vector counts, including the seven other cases recorded SKIP at all 102 settings per repaired variant, are preserved in summary.json. primary_index.json and paired_legal_outcomes.json link exact primary/UART/baseline paths and hashes.

## Oscillator fault probes: selected-case primary outcomes

|Variant|10-kHz slow probe|64-kHz fast probe|
|---|---|---|
|V0|fail|pass|
|V1|pass|pass|
|V1b|fail|pass|
|V2|fail|pass|

V1 accepts the slow-clock probe in its selected case. V1b and V2 assert-fail it, as does V0. All four selected cases pass the fast-clock probe. These are explicit primary verdicts, not finalized fault-detection claims: activation/control and task-specific reference review remain pending. The downstream case can fail even when the selected case passes; consult the full vectors.

## Next verification work (not executed here)

1. Reconcile assertion/source signatures for the short-relative and remaining single-shot failures; keep each case distinct from the repaired all-channels case.
2. Run only the originally registered representative same-input diagnostic replays and task-specific references in fresh paths after the required resource approval. Diagnostics never replace these primary records.
3. Verify each fault's activation and reference/control result before using detected/accepted language in the paper. Preserve the V1 selected-case slow-probe pass.
4. Reassess whole-application and cascade claims using same-run vectors; do not infer that cleanup failures disappear everywhere.
5. Revise the fourth-case paper material only after these checks. No E2, additional driver, new fault, retuned margin or broad study rerun.

All 30,067 original protected files passed before/after checks in each archive. Frozen scientific inputs and original records were not changed. Monitoring of these completed jobs is finished.
