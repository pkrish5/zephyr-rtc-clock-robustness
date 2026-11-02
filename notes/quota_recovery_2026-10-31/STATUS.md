# Quota recovery and S2-first continuation, 2026-10-31

## Latest checkpoint — S2 replays submitted, 2026-11-01 (supersedes all below)

S2 return 3544535 COMPLETED 0:0; archive `0de8c18e…` independently verified on
the Mac (1,122 records; 3,022 pass, 470 fail, 3,138 skip, 0 missing). Failures
remain unattributed. Roster frozen: 274 launches, 470 failures, identical to the
records-only draft (`notes/s2_attribution_2026-10-31/replay_plan_20261101_v1/`).

Storage check 3546137 FAILED at the runtime guard in 3 s (module load overwrote
`APPTAINER_CACHEDIR`; fixed). Rerun 3546138 COMPLETED and passed all 20 checks.
`run_packed.sh` now stops writers by session, because `timeout` escapes a group
kill.

**Replay job 3546149 submitted** at registered commit `2cf37d57`: normal,
TRA25006, one node, 01:00:00, at most 1 SU. PENDING (Resources) at first check.
Do not `git pull` on LS6 until it finishes; its code hashes are checked at start.

Next: transfer and verify its WORK archive under `tacc_work/packed-results/`,
compare against primaries, then attribution (a)–(d) per board and reconciliation
with isolated-case results. E, E2 and manuscript edits stay held.

## Earlier checkpoint — S2 return rerun submitted (superseded)

WORK read **686,770** files after 3544463 completed (0:0, 10:00), so the
below-700,000 target is **met**. Read-only inventory 3544399 COMPLETED 0:0.

S2 return **3544434 FAILED** (exit 127, 1:23) before the collector started:
inner `bash -l -c` had `set -u` active during `module load tacc-apptainer`,
whose bash-completion references unbound `BASH_COMPLETION_DEBUG`. Headroom
gate (686,766) and staging audit (30,067 unchanged) had passed. Reproduced on
a login node; the `set +u`/`set -u` fix exits 0. Registered in DESIGN.md
(commit `dd0bbd0a`, pulled on LS6).

Fixed adapter `s2_archive_scratch_v2.py`, SHA-256 `891054ae…b2a0`; only the
module-load wrap differs. Local protected audit before submission: 30,067
unchanged (`mac-protected-before-s2-return-v4.json`, audit SHA `e85964d5…`).
**3544535 submitted**, development/TRA25006, one node, 02:00:00, no
dependency, tag `s2-priority-return-20261031-v4`; receipt
`s2-return-submission-v4.json`. PENDING (Resources) at first check.

Next: on completion, transfer and independently verify the returned archive
(coverage, checksums, ELF and logs), then freeze and submit the pre-approved
replay job. E stays held until S2 is done; E2 and manuscript edits remain held.

## Earlier checkpoint (superseded)

**Current queue:** 3544463 PENDING Resources (replacement D archive),
3544434 PENDING afterok:3544463 (S2 collection), 3544399 PENDING
afterany:3544434 (read-only inventory). At 14:15 Central the scheduler
estimated 3544463's start at 14:17:02; this is not a guaranteed start.
3544431 was cancelled during its initial read-only inventory, before
any archive or deletion manifest existed, at 33:14 elapsed. See the
replacement evidence below. Latest completed cleanup file-count reading
remains 896,584 before that batch's three proof files; no below-700,000
result has yet been demonstrated. E, E2 and manuscript edits remain held.

Mac and LS6 both reached commit
`87249a2d1f4facc3b896bd1dd61efbd85c2cf616` by Mac push and LS6
`git pull --ff-only`; no scientific input or original record changed.

- **3544396 COMPLETED**, 15:22. Fifteen build records checked; 3,389
  regenerable leaves and 3,324 empty directories removed. All 30,067 protected
  hashes matched. WORK read 933,195 before its three proof files were added.
  The returned proof was independently checked on the Mac; see
  `batch-3544396/local-verification.json`.
- **3544417 COMPLETED**, 15:21. Eighty-four build records checked; 18,720
  regenerable leaves and 18,020 empty directories removed, with 31,990 retained
  file checks. All 30,067 protected hashes matched. WORK read **896,584** before
  three proof files were added. The returned proof archive SHA-256 is
  `c7b8ce9ffc1ad61569e7a9aa77a4adcefbe6750f7884adcede360d7dc2e0fe07`.
  Local verification confirms the identical protected maps and all 84
  historical recorded-ELF comparisons; see `batch-3544417/local-verification.json`.
- **3544431**, subsequently cancelled before pruning: full completed D-v2 output and separate closed runtime
  archival/verification, then pruning. Development, one node, 02:00:00,
  TRA25006, afterok:3544417. Source SHA-256
  `d58a267e6c022291c80fd96bb4c2bb5389d381a93a621d604e68ad0836faeb10`.
  Its final archive and compressed pre-deletion manifest must be on WORK before
  any loose output is removed. Historical hashes of all 216 D build records,
  ELFs and build logs are pinned to the previously verified D evidence.
- **3544399 PENDING**, read-only completed-output inventory, now
  afterany:3544434. This avoids racing D pruning and gives S2 priority.
- **3544434 PENDING**, S2 primary collection, now afterok:3544463. Development,
  one node, 02:00:00, TRA25006. Source SHA-256
  `95c8f79e53272093df6f639ebdb6ff1fce4fa5ed91c584f54ddd696c34104385`.
  A fresh quota check must be **below 700,000** before the unchanged collector
  starts. Collection, hashing and packaging use SCRATCH; only the checked
  archive and receipts are published on WORK. No new simulations or builds.

3544397 and 3544424 were cancelled while PENDING and never ran. The latter
was a narrower superseded-D build cleanup, replaced by 3544431's verified
full completed-D archive. No S2 replay/reference execution, E recovery,
E2, or manuscript edit has started at this checkpoint. The below-700,000
target is **not yet demonstrated**.

## User constraints and priority

Target current WORK quota usage **below 700,000** before scientific follow-up
execution, S2 evidence/attribution before E, E2 and manuscript edits held.
Archive/verify closed outputs before deleting loose unprotected leaves.
Protected original factorial records remain loose. Keep the checkout recovery
backup, frozen inputs, ELFs, build logs and hash metadata. New jobs use SCRATCH
for builds/loose output, node-local /tmp for private homes/caches/temp, and
verified final archives on WORK. The original frozen wrappers remain intact.

## Initial checks

Existing queue empty. WORK quota read **939,908** files, unchanged from the
last verified recovery. Jobs 3541113/3541116/3541156 remain COMPLETED.
No new E execution or model calls. The local pre-publication protection
check verifies **30,067 files, zero changed**; receipt
`mac-protected-before-publication.json`, SHA-256
`d906fb14c819cbbf2e384a46b6501e4fbd6e8193b7779d79c3fb4b008c415e2d`.

## Submitted infrastructure jobs

- **3544396**, development / TRA25006, one node, 30 minutes: next
  checkpointed 128-record cleanup batch; same verified source as 3541156,
  SHA-256 `f7719eb14d30fa5a389154e724ee4ebc779434d197975e918e3f70bda7d4d837`.
- **3544397**, same source/limits, originally afterok:3544396.
- **3544399**, development / TRA25006, one node, 30 minutes: read-only
  inventory of exact registered output directories. Frozen study/results
  replicas are not selected arbitrarily. Initially submitted independently,
  then changed to afterok:3544397 so it cannot race build cleanup.

The first batch was still in the full pre-deletion protected audit at 8–9
minutes, with no deletion progress/output yet. This is slow verification,
not evidence of a verdict failure or changed input. The next batch was
still PENDING and was cancelled without running, to replace only its
read-only audit with eight bounded hash-reader threads and per-1000-file
progress. Hash keys/digests and cleanup rules are identical; changed-file
rejection was checked locally. The running 3544396 was not interrupted.
The inventory dependency must be moved to the accepted replacement batch.

## Prepared infrastructure and registration

`archive_closed_outputs.py` checks exact member sets/types, extracted-stream
hashes, an unchanged original inventory, and a final checked WORK archive
before pruning any leaf. Its compressed verification manifest is on WORK
before deletion. All builds, ELFs, sources, build logs, hash metadata,
protected and sealed input paths remain loose. Partial E and S2 primary
are excluded from generic cleanup. A local round-trip checked regular
files, directories and a symlink without following an external target.
Target lists require returned inventory review and completion evidence.

`prune_superseded_d_builds.py` is prepared for the old, closed D attempt.
It verifies any recorded final ELF and logs; missing final ELFs in failed
builds do not become test successes. Extra executables remain sealed and
retained. This script has not been submitted.

The storage-only/S2-priority amendment was appended to paper/DESIGN.md
before any new S2 replay/reference or E retry. New runtime storage guard
and README are in harness/tacc_storage/. They do not modify original
harness logic or records. Future scientific wrappers must use the guard
and archive publication, not the legacy WORK-writing common.sh.

The S2 primary collector/selection code remains unchanged. It will use
its original sealed DESIGN snapshot through a read-only protocol view.
Normal replay/reference job estimates and concrete scripts must be
presented for standing submission approval; no normal job is submitted
at this checkpoint. The E recovery amendment/index audit remains later,
after S2.

## Dependency replacement and storage guard

**3544417** was accepted, afterok:3544396, to replace the unstarted batch.
Its source `prune_build_batches_parallel.py` has SHA-256
`68b1903078e3f690f2d8abf095d7c2e881e5b3be28aa2c63729dfae4e240fcf6`.
It checks the identical full protected-file set/digests with eight readers
and progress every 1,000 completed hashes. The candidate/retention policy and
128-record/15-minute limits are unchanged. 3544397 was cancelled PENDING
without running. The read-only inventory 3544399 now depends on 3544417.

A 12:14 elapsed diagnostic confirmed the running 3544396 had written its
full protected-before file and printed that all 30,067 hashes match. Its
Slurm counters showed 216,055,861 bytes read, 4,720,461 written and roughly
nine seconds CPU, supporting a slow metadata/read stage rather than heavy
CPU work. No deletion completion is claimed from this preflight checkpoint.

New storage utilities in harness/tacc_storage include a compute-node runtime
guard, below-700,000 quota gate, and non-destructive archive publisher. A
local temporary fixture checked publication/manifest hashes and preservation
of its original output. This is infrastructure verification, not a firmware
experiment. Scientific wrappers must call publication after stopping writers
and arrange a signal path before any scientific job is submitted.

## Preparation during D archival

The returned 3544417 proof independently passed archive SHA verification,
protected before/after equality (30,067 entries), and all 84 recorded ELF
comparisons. D archive 3544431 was still RUNNING at 16:18 with no stderr
error, no pruning receipt, and increasing Slurm disk-read counters. This
is not yet a below-700,000 quota result.

Prepared (not executed) a replay-roster generator that rejects provisional
metadata and an outer replay adapter calling the frozen S2 simulation body.
No primary or historical harness file changed. Source review of the exact
release's RTC model identified preserved subsecond phase across calendar
writes; final S2 explanation tables must account for phase and application
state, rather than transplant isolated-case counts/boundaries. See
`notes/s2_attribution_2026-10-31/FULL_APPLICATION_PHASE.md`.

## Serial I/O replacement before deletion

3544431 remained in its initial read-only inventory after more than30minutes.
Before cancellation, its report directory contained exactly
`protected_before.json` and `targets.json`: no original inventory, tar,
pre-deletion manifest or prune receipt existed. The script cannot enter
pruning until all those later checks and a verified WORK archive complete.
Cancelled only3544431 and retained its SCRATCH evidence; no pruning phase
was entered. Receipt `d-serial-cancelled/cancel-before-pruning.json`.

Prepared a replacement with eight bounded directory/file readers and bounded
archive prefetch. Local fixtures prove identical inventory, tar member order,
metadata and extracted content, including links, a large streamed file and
special-file rejection. AST comparison confirms `main`, `must_keep`,
`verify`, `snapshot`, `sha`, and `save` are unchanged. Same D target list and
historical216 build-record seals. Receipt `parallel-archive-local-check.json`.
New source SHA-256:
`5ffad5f1bfcfcf1c5dc7b576afde61ce202096cb4127c9a37938b708f9715283`.

Replacement **3544463** accepted on development /TRA25006, one node,
02:00:00; PENDING Priority at its first check. Its preflight will recheck all
30,067 protected files before any pruning. S2 **3544434** now waits for
afterok:3544463. Inventory **3544399** waits for afterany:3544434, giving
S2 priority and still permitting read-only diagnosis if its headroom guard
stops it. No E job or S2 scientific replay/reference job was submitted.

The earlier commit/pull **1f395d25ec9ffe25b58f7dd9140b6fa296455797** is
on both Mac and LS6. The source-model review copies were not added to the
Git commit; their immutable upstream URLs and hashes are in the committed
provenance note. The manuscript changes remain preexisting and excluded.
