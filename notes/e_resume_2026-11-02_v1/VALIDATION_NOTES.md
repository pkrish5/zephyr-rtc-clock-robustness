# Independent E recovery evidence checks, 2026-11-02

Only local analysis of returned archives is performed here. Sealed production
code, manifests, DESIGN snapshot, all test inputs and original records remain
unchanged. No LS6 pull, job submission, rerun or manuscript edit occurred.

The generic archive verifier checked four complete-state archives for exact
coverage, extracted byte hashes and both 30,067-file protected maps. New local
verify_chunk.py additionally checks exact disjoint task indices, job/node/image/
module provenance, frequencies, source/ELF seals, raw hashes, record/trace fields,
fault activation and score derivation, replay fields and reference outcomes.
All 5,700 selected tasks in chunks 0–3 are accounted for. All 144 explicit
failures have matching persisted-field and raw-trace replay evidence; the 26
legal-clock failure slots have passing task references (14 unique reference
records in chunk 2). No new finalized missing verdict was produced in these
chunks. The original 29 harness errors remain missing and excluded from retry.

Before its first successful complete pass, the new local checker had three
schema/path assumptions corrected against the frozen sources: relative and
absolute paths needed normalization; min/max tasks carry loop index 0 but the
original rtc_factorial_v2.py writes seed=None for endpoints; and worker_e.py's
write_new wrapper enriches stored reference records with 12 provenance fields,
while reference_results embeds the returned core dictionary. The checker now
validates that exact added-field set and all shared values. These were local
checker corrections, not experiment, source, verdict or record changes. The
successful verification outputs are in chunk-00/01/02/03-analysis-v1.

This checkpoint is operational and incomplete. The final repair-effect table
and Phase 3 before/after numbers wait for all remaining chunks and full evidence
reconciliation. E2 and paper edits remain held.
