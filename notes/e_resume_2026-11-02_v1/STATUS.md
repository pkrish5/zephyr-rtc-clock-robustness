# Latest checkpoint, 2026-11-03 04:05 America/Chicago

E chunk 5 / 3547930 completed 0:0 in 50:42. Its archive returned via BatchMode
rsync and passed exact inventory (11,714 entries), extracted-file hashes and
before/after protected checks. Independent validation verified all 1,437 indices:
1,410 pass, 27 fail, no new missing. All 27 failures match persisted replay
fields and raw trace hashes; no legal-clock failure slots needed references.
Archive SHA256: df516d3e5f8a39ea50b2129fa068e0529863a95d146e4e72fd59dcf6e9c3f804.

Six recovery chunks now cover 8,573 indices: 8,378 pass, 195 fail, zero new
missing; all 195 failure replays agree. The earlier 26 legal failure slots have
passing references. Original plus verified-new accounting is 16,397/17,375;
978 evaluations remain in final chunk 3547931, still PENDING at this check.
The 29 original finalized harness errors remain missing. These counts describe
operational reconciliation, not final repair effects.

No new jobs, cancellations or LS6 pulls. Fresh local protected audit: all
30,067 unchanged. Manuscript/PDF baseline hashes unchanged. Continue from the
final completed archive, then the original-E collector; Phase B/C remain gated
on that verified evidence. User already authorized C/D after the checkpoint.
Receipts: queue_checkpoint_20261103_1005_v1.json,
protected_after_chunk05_receipt.json; E checkpoint_chunks_00_05_v1.json,
verified-3547930-v1/verification.json and chunk-05-analysis-v1/*.json.

# Latest checkpoint, 2026-11-03 00:34 America/Chicago

E chunk 4 / 3547929 completed 0:0 in 40:10. Its packed archive and sidecars
returned successfully through BatchMode rsync. Exact archive inventory (11,688
entries), extracted hashes and before/after protection checks passed. Independent
per-index audit verified all 1,436 indices: 1,412 pass, 24 fail, no new missing;
24/24 persisted-field and raw-trace replay matches. No legal-clock failure slots
in this chunk required references; no mismatches or reference nonpasses.
Archive SHA256: 73dcd6f0db6c7ec763ed5536bb1b46458a7213ac4457e42d2934471b7868ca0e.

Five chunks now total 7,136 verified new indices, 168 exact failure replays and
26 reference-supported legal failure slots. Together with the 7,824 retained
originals, 14,960/17,375 are accounted for, with 2,415 still outstanding. Original
29 finalized harness errors remain missing. These are operational accounting
numbers, not final repair-effect statistics.

3547930 and 3547931 remain PENDING at the one scheduled status check. No LS6
pull or job submission/cancellation occurred. Local protected audit passed all
30,067 files; draft/PDF match their baseline hashes. Phase B remains gated on
the remaining chunks and the original-E evidence collection. Automatic C/D
continuation is authorized after verified evidence, with no human Phase 3 stop.
Receipts: queue_checkpoint_20261103_0634_v1.json,
protected_after_chunk04_receipt.json; E checkpoint_chunks_00_04_v1.json,
verified-3547929-v1/verification.json and chunk-04-analysis-v1/*.json.

# E quota-interruption recovery, 2026-11-02

## Latest checkpoint — four E chunks independently verified, 2026-11-02

3547925/26/27/28 completed 0:0 in 35:50 / 37:25 / 33:29 / 35:23.
Their archives were returned and independently checked for exact inventory,
byte hashes, per-index identity, source/ELF/frequency seals, raw traces,
actual job/module/node provenance, fault-score derivation and follow-ups.
5,700/5,700 scheduled indices are complete: 5,556 pass, 144 explicit fail,
zero new finalized missing outcomes. All 144 failures match fresh-process
replay fields and raw trace hashes; the 26 legal-clock failing slots have
passing references (14 unique reference records). No reference nonpass or
replay mismatch. Every job checked all 30,067 protected hashes and 35,708 old
E evidence files before/after. A new local protected audit also passed.

The original 7,824 completed records remain as audited, including 29 finalized
harness errors. Original plus verified-new accounting is 13,524/17,375;
3,851 indices remain. This is an operational checkpoint, not a final repair
study result or a paper-number change. Phase 3 waits for full reconciliation.

Latest read-only check after verification: 3547929 still PENDING (Priority),
3547930 and 3547931 PENDING (Dependency), no starts. No new jobs, cancellations,
resubmissions or LS6 git pulls occurred. Do not pull while any chunk is pending
or running. Retain the original 21-SU reservation ceiling; no extra job budget
is added here. E2 and manuscript edits remain held.

Receipts: status_after_chunks_00_03_v1.json and checkpoint_chunks_00_03_v1.json.
Detailed verification: verified-3547925/26/27/28-v1/verification.json and
chunk-00/01/02/03-analysis-v1/. VALIDATION_NOTES.md records local checker schema
corrections against the frozen sources; no run or record was changed.

## Latest checkpoint — seven E recovery jobs accepted, 2026-11-02

All seven scoped normal submissions accepted under TRA25006, one node and
32 Launcher workers each, three-hour limits, 3-SU ceilings (21 total).
Last checked all PENDING: 3547925 for Priority; six successors for Dependency.
Receipt: resume_submissions_v1.json; verification: resume_initial_status_v1.json.
Clean LS6 HEAD matched registration
commit f25ac1b65a793d24bef792c14a13c87062026ad3. Never git pull while any job
is pending/running: the jobs verify this registered code and DESIGN snapshot.

| Chunk | Job | Eligible indices | Dependency |
|---|---|---:|---|
| 0 | 3547925 | 1436 | none |
| 1 | 3547926 | 1437 | afterok:3547925 |
| 2 | 3547927 | 1392 | afterok:3547926 |
| 3 | 3547928 | 1435 | afterok:3547927 |
| 4 | 3547929 | 1436 | afterok:3547928 |
| 5 | 3547930 | 1437 | afterok:3547929 |
| 6 | 3547931 | 978 | afterok:3547930 |

Exact disjoint union: 9,551 audited incomplete/not-started indices; no completed
original, including finalized harness error, is selected. Old inputs, ELFs,
execution seals, STOP, partial bytes and complete records are read only. New
job outputs are on SCRATCH with checked WORK archives. No E result is yet
verified; acceptance is not completion. Do not rerun completed jobs/indices or
blindly retry an interrupted submission. On completion verify each archive and
chunk result, recheck all original hashes, union by index with provenance and
report missing outcomes separately. Stop on any integrity or process failure;
later dependencies prevent subsequent chunks from executing after failure.
E2 and manuscript edits remain held. STOP at Phase 3 before/after number table.

## Latest checkpoint — fixture verified; normal chunks sealed, 2026-11-02

3547838 completed 0:0 in 7:05. Independently verified its exact 119-entry
archive (0b7ed7e5…), all 32 container mount probes, sealed metadata, 35,708
unchanged retained E evidence files and both 30,067-file protection receipts.
No builds/firmware ran. WORK publication count 687,233 passes the E gate.
All 7,824 saved worker resource profiles are complete: median/p95/max elapsed
34.845/110.1/320.79s, max peak RSS 331,924 KiB.

Seven exact ordered, disjoint normal chunks contain 1,436 / 1,437 / 1,392 /
1,435 / 1,436 / 1,437 / 978 indices. Total 9,551 eligible; zero completed
originals selected. Each is one node, 32 Launcher workers, <=03:00:00,
TRA25006, ceiling 3 SUs each / 21 total. Plan faaed0c9…, production code/input
manifest ebd8424c6fab92ec31392aa8d03aa3384b1c5d4e233b4524b54773d1d59e8a15.
Dated DESIGN registration and direct-user scoped approval receipt precede runs.
Before submitting, commit/push, git pull on LS6, verify clean matching HEAD and
queue. Submit once per chunk only as queue limits allow, chained afterok to
prevent further evaluation after a failed chunk; reconcile uncertain acceptance.
No normal job is submitted yet. Never pull while any chunk is pending/running.
E2 and manuscript edits stay held; stop at Phase 3 before/after number table.

## Latest checkpoint — storage qualification submitted, 2026-11-02

Development job **3547838** accepted: TRA25006, one node, 02:00:00,
reservation ceiling 2 SUs, no requeue, ten-minute publication reserve.
Last checked PENDING, start/end Unknown. Receipt fixture_submission_v1.json.
Clean LS6 HEAD matched Mac/origin
registration commit a632aec72c5079685dcbda9944adc99f6994ac78.
No normal job or E primary evaluation has been submitted. Do not git pull while
this fixture is pending/running: it checks the sealed DESIGN and code hashes.

Next: independently verify the completed fixture archive and all mount checks,
read its full-worker resource profile, then freeze exact disjoint <=3h normal
chunks of the 9,551 eligible indices and report concrete SU estimates under
the user's scoped E recovery approval. Any fixture anomaly blocks submission.
Complete originals, including 29 finalized harness errors, stay unchanged.
E2 and manuscript edits remain held.

## Latest checkpoint — E audit verified, fixture prepared, 2026-11-02

Audit 3547562 completed 0:0 in 27:08. Returned archive f359400f… is independently
verified (16 exact entries, internal hashes, both protected checks). Classification:
7,824 complete and valid (7,549 pass, 246 fail, 29 finalized harness errors),
1 incomplete (7979), 9,550 not started, 0 anomalies, 0 missing derived follow-ups.
The 29 saved harness errors remain missing and will never enter recovery.
WORK publication count 687,145 passes the 700,000 E gate.

Exact retry list: packet/retry_indices.json, 9,551 indices, SHA-256 3b2c6728…;
selection seal 3e4d45cb…. Dated DESIGN amendment is written before any resumed
run. PROTOCOL.md and new infrastructure-only adapters qualify original read-only
mounts and SCRATCH overlays without invoking Renode, a compiler or the E worker.
They also profile saved full-worker timings to budget later normal chunks.
The development fixture is prepared but not yet submitted: one node, two hours,
TRA25006, at most 2 SUs. It must pass archive/hash/mount verification before any
normal recovery submission. No E evaluation has resumed. E2/paper edits held.
Fixture manifest: 804df2c9b5111accb65222c57e07dfc6b9a28863f3ac87d7325eb883560857ff.
Local protected audit again reports 30,067 unchanged; manuscript unchanged.

## Latest checkpoint — read-only audit submitted, 2026-11-02

User reconnected and authorized continuation. BatchMode access succeeded;
queue was empty. LS6 git pull reached Mac/origin commit
78137bf4aac0e63556dde2bed423cceaddc9cd6c with clean status.
Development job **3547562** was accepted: TRA25006, one node, 02:00:00,
reservation ceiling 2 SUs, no requeue and ten-minute packing signal.
Receipt: `audit_submission_v1.json`. One subsequent read-only sacct check
reported PENDING, start/end Unknown. No simulations or resume job submitted.

Next: when this job finishes, inspect its logs and packed-state receipt,
transfer its new archive, independently verify the exact inventory, hashes,
protected checks and classifications. Any integrity anomaly stops resumption.
Only then freeze retry indices and the dated DESIGN amendment. E2 and paper
edits remain held. Do not pull while this job runs; do not resubmit it blindly.
The earlier authentication-stop account below is retained as history.

## Current state

S2 reference validation is complete and independently verified; see
`notes/s2_reference_2026-11-02_v1/REFERENCE_RESULTS.md`. All 470 failing primary
slots have reference links. No E audit or E resume job has been submitted.
E2 and manuscript edits remain held.

The first E audit submission connection was rejected before the remote Python
command ran, with TACC password/MFA instructions and SSH exit 255. Remote access
stopped; no retry, authentication, checkout pull, namespace creation, or Slurm
submission occurred. Receipt: `audit_attempt_auth_rejected_v1.json`.
This is not an ambiguous sbatch acceptance. The user must reconnect and confirm.

Mac/origin code commit **71f1d04fe65c17640435896e1179467b0abddc52** contains the
read-only audit wrapper and reference results. LS6 was last verified at
3fa39cc8; do not assume the failed connection pulled 71f1d04f. Later Mac commits
may add status only. After reconnection use git pull only, then verify HEAD and
clean status before the single development submission.

## Prepared audit

`launch_audit.py` is compute-only infrastructure. It checks the SHA-256 of the
unchanged original auditor:
`43364d36d82af2725a45fc33db5db45fc47a6d164c84bf9192670400eb47e952`
for `notes/quota_recovery_2026-10-29/audit_e_partial.py`. It execs the proven
packed storage coordinator, with source output
`$SCRATCH/zephyr-rtc-clock-robustness/jobs/JOBID/output/e_audit` and label
`e-partial-audit`, before/after full protection checks and fresh WORK headroom
checks. It reads old E data without simulating, building, rerunning, deleting,
or modifying it.

Planned job: development/TRA25006, one node, two hours, reservation ceiling
2 SUs, no arrays, `--no-requeue --signal=B:USR1@600`. The batch wrap must be
`exec python3 <repo>/notes/e_resume_2026-11-02_v1/launch_audit.py`, so exec reaches
the coordinator in the batch PID and its USR1 packing trap receives the signal.
Use new SCRATCH submission directory
`$SCRATCH/zephyr-rtc-clock-robustness/e-partial-audit-20261102-v1` (it was not
created because authentication failed); write an acceptance receipt before
claiming any job ID. Never blindly retry a timeout or ambiguous submission.

Original data:
`$WORK/zephyr-rtc-clock-robustness/tacc_work/20261024-repair-v1/e-bundle`.
The original E job 3535400 failed on WORK quota; preserve its STOP marker,
partial files, completed records, build products, controls and all old hashes.
The reference image remains 94d7894e…aaa1 and the modules are
tacc-apptainer/1.4.1 and launcher/3.10. Every job uses -A TRA25006.

## Required gates before resumption

1. Transfer and independently verify the new audit archive and protected
   receipts. Inspect every integrity anomaly before proceeding. Incomplete
   entries are not the same as finalized harness-error missing verdicts.
2. Preserve complete-and-valid primary records exactly, including fail, error,
   timeout and other saved missing outcomes. Do not rerun a primary just because
   its derived score/replay/reference follow-up is missing.
3. Freeze exact incomplete and not-started evaluation indices from the audit,
   with execution/task/source/ELF seals. Add the dated DESIGN amendment:
   quota-interrupted evaluations without a final verdict may run again;
   completed records stay as is; finalized harness errors stay missing.
4. Register separate new output namespaces. Old logical paths may be preserved
   through SCRATCH overlays, but original files and sealed metadata/ELFs must
   remain read only. Never copy or ignore the old STOP marker in place.
   Use the original evaluation body and actual new provenance, no rebuilds.
5. Use the audit and saved per-index timing/resources to estimate chunks with
   packing/protection reserve. Each normal chunk is at most three hours;
   report nodes, wall time, SUs and job IDs under the user's existing scoped
   E-resume approval and standing normal-submission rules. Only incomplete or
   not-started primary indices may be selected. No duplicate submission or
   automatic requeue. Pack verified outputs to WORK; never leave final records
   only on SCRATCH. Fresh WORK count must remain below 700,000 for E.
6. STOP at Phase 3 with the before/after number table before paper edits.

Always use SSH/rsync BatchMode. Stop on credential requests, connection drops,
or stalled remote operations. Do not touch ~/.ssh or account settings. The
handoff's user-side keepalive command, if they choose to use it, is
`ssh -fNM -o ServerAliveInterval=60 -o ServerAliveCountMax=5 ls6`; the user
must authenticate themselves. Never edit/stage/commit their main.tex or main.pdf.
