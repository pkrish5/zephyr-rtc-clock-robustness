# Conditional S2 replay submission proposal, 2026-10-31

Not submitted. No new firmware executions or builds. User normal-queue
approval is required under the standing rule.

- Work: one unchanged full-application replay for each original launch with
  an assertion failure; preserve every case and capability skip.
- Queue/account: normal, `-A TRA25006`.
- Nodes/wall limit: one node,01:00:00,32 local TACC Launcher3.10 workers.
- Estimated throughput from saved primary runtime:0.163 node-hours with
  a1.5 allowance. Auditing,filesystem overhead and packing are additional.
- Budget estimate:up to1 SU; reservation ceiling1 SU. TACC bills at least
  0.25 SU for a normal job even if it finishes in less than15minutes.
  Source verified2026-10-31:
  https://docs.tacc.utexas.edu/hpc/lonestar6/#job-accounting
- Exact conditional roster:274 launches covering470 observed case failures,
  listed in `replay_candidates_RECORDS_ONLY.csv`. These counts are currently
  from the earlier record-only copy, not the completed raw-evidence audit.
- No rebuilds, test edits, deadline changes, isolation or original-record
  replacement. No E/E2 or reference execution is included in this job.

## Conditions that must all hold before submission

1. WORK below700,000; S2 full archive transferred and checksum/coverage/log/ELF
   audits independently agree.
2. The full audit produces exactly this index roster, original-record hashes
   and source trace hashes. Any difference invalidates this conditional plan
   and must be reported before submission.
3. New compute-node fixture confirms original inputs/builds are read only,
   new output on SCRATCH, private node-local runtime, and verified WORK
   publication after a controlled interrupt with no surviving writer.
4. Register the exact verified replay plan and code hashes in DESIGN.md before
   execution. Record explicit user approval and report actual job ID/SUs
   on submission. Missing or mismatching replays remain separate from primary
   scores. New references require their own frozen source/protocol and
   submission gate.

Candidate CSV SHA-256: `2f6508ae5302666847ac83ca15643a0a159d5c685e44de9fb2eec8d983121f10`.

Scripts: `harness/tacc_s2_evidence/{prepare_replay_plan.py,replay_worker.py,
setup_replays.py,replay_task.sh,replays.sbatch,seal_replay_packet.py}` and
`harness/tacc_storage/`. They are new outer storage/provenance adapters;
the original S2 simulation implementation remains byte-identical.
