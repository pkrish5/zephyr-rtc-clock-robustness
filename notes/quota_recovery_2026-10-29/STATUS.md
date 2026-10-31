# Quota recovery checkpoint, 2026-10-29

The user's ordered recovery authorization starts with read-only diagnosis.
No deletion is authorized by this note; cleanup must stop if the largest
sources are unexpected or a proposed deletion intersects protected paths.

## Submitted diagnosis

Job **3540537**, development / TRA25006, one node, 30-minute limit.
The exact source is `diagnose.py` alongside this note, SHA-256
`724d267c8082c69aa5362a123648eb2d575542bb9812703206f2a0948a096160`.
The accepted receipt is `submission.json`. It is a metadata-only scan:
no test builds, no simulation, no verdict analysis, no deletion, and no
WORK output files. The Slurm script was submitted via stdin-controlled
job orchestration and retained in SCRATCH; no repository code was synced
outside the standing Git-pull workflow.

Source: all entries under `/work/10970/pk23377/ls6`, without following links
or crossing device boundaries. It reports directory entries and distinct
inode counts, per top-level directory and TACC attempt, plus cache/build/
runtime/evidence categories and protected-path presence. The frozen
baseline is checked by its original SHA-256 before scanning.

Report directory:
`/scratch/10970/pk23377/zephyr-rtc-clock-robustness/quota-recovery-20261029-v1/scan`.
Scheduler logs: `diagnose-3540537.out` / `.err` in its parent.
Fetch and independently verify `files.sha256.json` and the report files
locally before drawing cleanup conclusions. No file counts are final yet.

## Latest verified progress

The last successful scheduler check returned RUNNING, elapsed 00:02:52,
node c307-005. Its log reported 100,000 directories visited and 417,185
entries at 147.5 seconds. This is partial scan progress, not the final
inode inventory or a count of regular files.

Before submission, WORK quota was 1,024,001 files against a 1,024,000-file
soft quota, while byte usage was below its quota. No other jobs were
running at the initial check. No quota was changed.

## Connection interruption

The unrelated Buddi message was withdrawn by the user. No deck edits were
made. The work resumed on this quota-recovery task.

An automatic permission-review timeout prevented one later status check
from starting; its one permitted retry then encountered
`mux_client_request_session: read from master failed: Broken pipe`.
Only that local SSH client was stopped. Remote access paused under the
standing connection rule; the running Slurm diagnostic was not cancelled.
No authentication was attempted.

Resume by reading the existing job's state and reports after the user
reconnects. Do not submit a duplicate scan. Steps 2–5 have not started:
no cleanup, packing/deletion, dependency removal, E classification/resume,
or S2 archive retry. The E recovery amendment is not yet written because
the Step 1 stop gate has not been evaluated. E2 and manuscript edits remain
on hold. Complete original records, frozen sources/forecasts, and the
checkout recovery backup are untouched.

## Reconnected checkpoint

The diagnosis completed successfully (3540537, 0:0, 00:06:51). All eight
returned report files passed their SHA-256 manifest; see STEP1.md for the
verified inventory and protected exclusions. Expected build/cache/runtime
trees dominate. The Step 1 stop gate was evaluated for one narrowly scoped
candidate and did not trigger.

Guarded bootstrap cleanup **3540791** is submitted on development, TRA25006,
one node, 30-minute limit. It independently verifies the existing complete
A–B archive, exact member coverage and every extracted file hash before
removing only the matching completed loose A–B output. Original protected
paths, frozen bundle inputs, ELFs/logs and the checkout recovery backup are
excluded by guards. The archive remains on WORK. The accepted receipt is
bootstrap-submission.json; source is bootstrap_ab.py.

At the latest reconnected check it was PENDING (Priority). No deletion has
been observed; no E resume or S2 archive retry has been submitted. The build
intermediate cleanup script and E classification protocol are prepared, not
run. The existing 485 absent protected paths remain a provisioning issue,
not a successful full-baseline audit.

## Dependent cleanup submissions

- **3540816**: development / TRA25006, one node, 30 minutes,
  `afterok:3540791`. Deletes only allowlisted E and D v2 build intermediates
  after recorded ELF/log and frozen-input checks. Source:
  `prune_build_state.py`, SHA-256
  `292b233c60edd1a37796a53815c080e1554a648fff7944735d52fc6d70d05c3f`.
- **3540821**: development / TRA25006, one node, 30 minutes,
  `afterok:3540816`. Compares the abandoned v5 Python package versions and
  Renode DLL with the retained calibrated SIF; removes only matching
  duplicate package trees. Mismatches remain. Zephyr source, frozen harness
  copies, SDK trees and backup are excluded. Source:
  `prune_duplicate_dependencies.py`, SHA-256
  `17b33282b4f652939509c162e627bcfe733274b9855d841eceadfe3a78d08feb`.

An attempted fourth development submission to finish original audit-input
restoration was rejected before receiving a job ID:
`QOSMaxSubmitJobPerUserLimit`. The rejected receipt is
`audit-restoration-rejected.json`. It ran no commands on a compute node and
restored no files. Retry only after a submission slot opens, with a fresh
tag and receipt. This is a submission rejection, not a failed experiment.

The local Mac protected-file check after preparing infrastructure scripts
verified all **30,067** original files with **zero changed**. Receipt:
`mac-protected-after-preparation.json`, SHA-256
`def880e69c604e5e3c1f4d9a2a28aacf5db3f8cb5024ecb96e23fa72b89d0296`.
This does not substitute for the pending full LS6 audit.

Prepared but not submitted: `restore_audit_inputs.py`, `audit_e_partial.py`,
and `s2_archive_scratch.py`. The latter keeps the original S2 collector and
selection code unchanged, uses the original registered DESIGN snapshot,
and puts its loose archive workspace on SCRATCH through a container bind.
Its final checksummed archive will be copied to WORK. None of these
prepared scripts has yet run. No DESIGN amendment, E evaluation retry,
normal-queue submission, or manuscript edit has occurred in this recovery.

Latest scheduler estimate moved the bootstrap start to approximately
14:01:47 Central; this is a changeable scheduling estimate, not a promise.
All three cleanup jobs were still pending at that check. No after-cleanup
file count is available until their verified receipts are returned.

## Completed bootstrap and timed-out build inventory

Read-only accounting confirmed **3540791 COMPLETED 0:0 in 00:11:03**.
The returned proof archive matched SHA-256
`da977541198be50e35609b3dcc4a38cae728cbc0d41f9b15fc221edfc06fb754`.
Local verification of its contents confirmed exact coverage of all 13,070
entries (13,060 regular files), extracted-content hashes, and matching
protected-before/after maps: 29,582 present originals unchanged, with the
same 485 pre-existing absent paths. The completed A–B output was removed
only after these checks; its raw archive remains on WORK and the Mac.
Receipts and independent check: `bootstrap-verified/`.

Quota accounting fell from **1,024,001** to **1,010,931** immediately after
pruning, then **1,010,935** after retaining proof metadata. A fresh read
still returned 1,010,935. Net reduction including proof files: **13,066**.

**3540816 TIMEOUT**, elapsed 00:30:28, batch cancelled with signal 15 on
c306-006. Exact stderr:

```text
slurmstepd: error: *** JOB 3540816 ON c306-006 CANCELLED AT 2026-10-29T15:14:43 DUE TO TIME LIMIT ***
```

Its stdout was empty, and the only report was `protected_before.json`.
That report verifies the 29,582 present original hashes and lists the same
485 absent paths with no changed hashes. The program writes its keep and
deletion manifests, and a progress line, before any unlink call; none was
reached. Thus this attempt timed out in pre-deletion inventory/hash work,
not during deletion. Exact build unit at interruption is unknown because
that old version did not emit per-unit progress. Logs and audit retained in
`build-prune-timeout/`. This is one consecutive failed cleanup execution.

**3540821** was blocked with `DependencyNeverSatisfied`; it was cancelled
without running. No package trees were removed by it.

## Infrastructure-only correction and new jobs

The new `prune_build_batches.py` preserves the deletion allowlist and
protection rules, processes at most 32 build records, records each unit's
manifest before deletion and verifies retained bytes afterward. It stops
starting units after 15 minutes including preflight, reserving the remaining
half of the development allocation for final input/protected checks and
packing. Disposable intermediates use stat/link identities; final ELFs,
logs, sources and retained files use SHA-256. All final ELF hashes must
match their historical build records. No original harness, source, ELF,
forecast, verdict or archive-selection code was changed. Candidate guards
were checked locally; no scientific test was run.

- **3541113**: development / TRA25006, one node, 30 minutes, standalone.
  Restores only absent original audit dependencies from verified cache and
  runs the unchanged full 30,067-file protection audit. Existing paths are
  never overwritten. Source `restore_audit_inputs.py`, SHA-256
  `a13d5a84b4162ea8cbcaa9da996515fc9df544f7a8006308e9462c28dd35b005`.
- **3541116**: development / TRA25006, one node, 30 minutes,
  `afterok:3541113`. First checkpointed cleanup batch. Source
  `prune_build_batches.py`, SHA-256
  `23cef3c233fa972cfd61c8372f94d58bcde5292ea77cd358781ba661ee9aad62`.

Accepted submission receipts are `audit-restoration-v2-submission.json` and
`build-batch-v2a-submission.json`. Their completion and after-cleanup count
are not yet confirmed. Duplicate-dependency cleanup and the unchanged S2
collector's storage wrapper were updated locally to require the new batch's
success receipt; neither replacement has been submitted. No E retry, E2,
normal-queue job, new experiment, DESIGN amendment or manuscript edit was
performed at this checkpoint. Stop on protected-hash differences or after
three consecutive failed infrastructure executions.

## Replacement jobs independently verified

Read-only accounting returned **3541113 COMPLETED 0:0 in 00:01:16** and
**3541116 COMPLETED 0:0 in 00:02:25**. Both used development / TRA25006.
The retrieved restoration receipt confirms 485 original missing files were
restored, zero pre-existing paths overwritten. Its full protection report
checks all **30,067** original files with zero changed hashes.

The returned batch proof matched SHA-256
`baf1b0b1d780a7db0a65f52e4b13851d13bf98673f62b4eecacbaeb1f8790264`.
Independent local checks confirmed matching full protected-before/after
maps and disjoint disposable/retained sets for each verified unit. The
batch processed 32 build records, removed **7,280** regenerable leaves and
**7,028** empty directories, and verified **12,443** retained-file checks.
No protected source, raw verdict, final ELF, build log or backup was removed.
574 build records remain eligible for consideration. Source receipts:
`replacements-verified/`, including `local-verification.json`.

The batch quota snapshot was 1,011,744 before deletion (after original audit
dependency restoration) and **997,436** after pruning, before its final proof
files. This is not the final overall recovery count. The full protected
audit now passes on LS6, resolving the earlier 485-path provisioning gap.

Given the measured 139.6-second cleanup processing time, subsequent batches
allow at most 128 records while retaining the whole-pass 15-minute soft
cutoff and 30-minute allocation. Each unit still checkpoints before/after
and verifies historical ELF/log hashes; completed units are skipped using
verified prior receipts. Only metadata batching changes. The successful
restoration and batch reset the consecutive failed-infrastructure count.

## Submission connection timeout after successful replacements

The next metadata-only cleanup submission used tag
`quota-build-batch-20261029-v2b` (128-record cap, unchanged 15-minute soft
cutoff), development / TRA25006, one node / 30 minutes. The local SSH
subprocess timed out after **120 seconds** without returning a job ID or
stdout. It was stopped by the local subprocess timeout; the existing SSH
master, account settings and Slurm jobs were not changed. Acceptance by
Slurm is **unknown**. See `build-batch-v2b-submission-unknown.json`. This is
not evidence of a failed or absent remote job. Do not resubmit it blindly.

Under the standing connection rule, remote access stopped. The user was
asked to confirm WORK/session responsiveness. After confirmation, inspect
the existing SCRATCH tag's submission JSON/attempt and Slurm queue/accounting
to reconcile this attempt. If a job ID exists, monitor that job; never
create a duplicate. No duplicate-dependency job, E audit/resume, S2 archive
retry, normal-queue job, E2 or manuscript edit was performed. The last
verified completed stage remains the full protected audit plus first
32-record cleanup batch; the next batch's results are not yet known.

## Reconciled submission and user-requested report hold

The user confirmed WORK responsive and an empty queue, and requested that
failed original cleanup jobs be reported before any submission. Read-only
accounting and log reads confirmed:

| Job | State | Exit | Elapsed |
|---|---|---|---|
| 3540791 | COMPLETED | 0:0 | 00:11:03 |
| 3540816 | TIMEOUT | batch 0:15 | 00:30:28 |
| 3540821 | CANCELLED without running | 0:0 | 00:00:00 |
| 3541113 | COMPLETED | 0:0 | 00:01:16 |
| 3541116 | COMPLETED | 0:0 | 00:02:25 |
| 3541156 | COMPLETED | 0:0 | 00:05:44 |

The original timeout stderr was reread and is the same time-limit message
already preserved above; stdout is empty. It occurred before its deletion
manifest/progress message and therefore before any deletion in that attempt.
The blocked dependency was deliberately cancelled and never ran.

The empty queue did **not** establish non-acceptance of the timed-out client
submission. Its existing SCRATCH receipt confirms acceptance as **3541156**,
which had already completed. Its source hash is
`f7719eb14d30fa5a389154e724ee4ebc779434d197975e918e3f70bda7d4d837`,
matching the locally prepared 128-record batch source. No duplicate was
submitted. This resolves the prior unknown submission state.

The returned batch archive matched SHA-256
`1f204261b5cea0e979dfa55bafde695e38e07dfef0bc9bb6e6350daf6e2efaba`.
Local proof checks verified all 128 checkpointed build records, disjoint
retained/deleted sets, and identical 30,067-file protected-before/after maps.
It removed **29,158** regenerable leaves and **28,376** empty directories.
446 build records remain. Full receipt and independent local verification:
`batch-v2b-verified/`.

A fresh WORK quota read returned **939,908 entries**, down **84,093** from
the original 1,024,001, including restored original dependencies and retained
proof files. The second batch's own pre/post counts were 997,439 / 939,905;
its three final proof files account for the current 939,908. Archive coverage
and extracted-content verification for the completed A–B raw results remain
confirmed by the retained bootstrap proof and Mac checks. Its raw archive
remains on WORK. No frozen sources, forecasts, raw verdicts, ELFs/logs or
recovery backup were deleted.

No jobs were submitted during this reconciliation. In accordance with the
latest instruction, report the original failed cleanup and the successful
replacements before any further submission. Dependency-package cleanup,
remaining build cleanup, E audit/resume and S2 evidence collection remain
pending; E2 and manuscript edits remain on hold.
