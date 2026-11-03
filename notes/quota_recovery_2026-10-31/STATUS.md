# Quota recovery and S2-first continuation, 2026-10-31

## Latest checkpoint — E chunks 0–3 verified; three still queued, 2026-11-02

3547925–3547928 completed 0:0; all four archives independently verified.
5,700 new indices: 5,556 pass, 144 fail, no new missing. 144/144 failure
replays match; references pass for all 26 new legal-clock failures. Protected
and old-E hashes unchanged. Accounted original+new: 13,524/17,375, with the
29 original finalized harness errors preserved. 3,851 indices remain.
3547929 PENDING Priority; 3547930/31 PENDING Dependency. No new submissions
or LS6 pulls. See notes/e_resume_2026-11-02_v1/STATUS.md and receipts.
E2/paper held; Phase 3 before/after table still waits for complete evidence.

## Latest checkpoint — E normal recovery submitted, 2026-11-02

3547925, 3547926, 3547927, 3547928, 3547929, 3547930, 3547931 accepted,
normal/TRA25006. One node / 32 workers / <=3h / ceiling 3 SUs per job,
21 SUs total, serial afterok chain. Exactly the 9,551 audited eligible indices;
all complete originals and 29 finalized missing outcomes are excluded. No
outcomes verified yet. Never pull LS6 while these sealed jobs are pending or
running (registered commit f25ac1b6). Receipt and next verification steps are
in notes/e_resume_2026-11-02_v1/STATUS.md. E2/paper held; Phase 3 stop remains.

## Latest checkpoint — E recovery ready for approved normal submission, 2026-11-02

3547838 passed independent archive/mount/protected/original-record validation.
Seven <=3h one-node chunks cover exactly the 9,551 audited eligible indices;
ceiling 3 SUs each, 21 total, TRA25006, 32 workers, afterok chain. No normal
recovery job submitted yet. Registration/plan/code seals and qualification
results: notes/e_resume_2026-11-02_v1/. Original 29 harness errors remain
missing. E2/paper stay held, with Phase 3 stop before any paper edit.

## Latest checkpoint — E storage qualification accepted, 2026-11-02

3547838 accepted on development/TRA25006, one node, two-hour limit, ceiling
2 SUs; registration commit a632aec7. No firmware/builds in this qualification.
Do not pull LS6 until it finishes. E normal resumption awaits verified mount
checks and saved timing profiles. See notes/e_resume_2026-11-02_v1/STATUS.md.

## Latest checkpoint — E audit verified, before resumption, 2026-11-02

3547562 completed 0:0, 27:08. Independent verification: 7,824 complete,
1 incomplete, 9,550 not started; 0 integrity anomalies or missing follow-ups.
Preserve 29 finalized harness errors. Exact 9,551-index recovery list and dated
amendment frozen in notes/e_resume_2026-11-02_v1/packet/ and DESIGN.md.
WORK 687,145 at publication. Infrastructure-only development mount fixture is
prepared, not yet submitted; no evaluations resumed. E2/paper remain held.

## Latest checkpoint — E read-only audit accepted, 2026-11-02

After user reconnection, BatchMode access succeeded and clean LS6 HEAD matched
Mac/origin 78137bf4. Job **3547562** accepted on development/TRA25006, one node,
two-hour limit, reservation ceiling 2 SUs. Last verified PENDING. It uses the
unchanged original auditor and new packed SCRATCH output; no E evaluation has
resumed. Receipt and next verification gates are in
`notes/e_resume_2026-11-02_v1/`. E2 and manuscript edits remain held.

## Latest checkpoint — S2 references complete, E audit blocked by SSH

2026-11-02: reference results verified and pushed in 71f1d04f. The first
connection to pull that code and submit the read-only E audit was rejected
before its remote command ran (BatchMode exit 255, password/MFA instructions).
Stopped with no retry. No E audit/resume job was submitted; LS6 is still last
verified at 3fa39cc8. User reconnection requested. Exact prepared audit and
resumption gates: `notes/e_resume_2026-11-02_v1/STATUS.md`.

## Latest checkpoint — S2 references verified; E audit next, 2026-11-02

Reference job 3547096 COMPLETED 0:0 in 39:00. Independent Mac verification of
archive 7b4ce8ae… confirmed 3,137 entries, raw/ELF/config/log hashes, all 351
reference records and both 30,067-file unchanged protection checks. Qualified
77 launches; evaluated all 274 failure-setting launches, covering every one
of 470 original failures, with no missing outcome or harness error.

277 waiting-failure slots passed references; 88 clean-state single-shot passes
leave the original cascades classified separately. All 105 seconds-rate slots
failed the retained rate reference while legal-clock progress passed; these
are flagged firmware/simulator or accuracy-contract investigation, not test
brittleness. F767 remains an F4 configuration replica, and phase is supported
but not directly measured. Full results and updated per-failure attribution:
notes/s2_reference_2026-11-02_v1/REFERENCE_RESULTS.md and verified-3547096-v1/.

Latest reference publication headroom was 687,073 WORK files, below 700,000.
Next: unchanged E partial-index audit on development with packed new output,
then freeze a dated infrastructure-interruption amendment and exact retry
list before any evaluation resumption. E2 and paper edits remain held.

## Latest checkpoint — reference job 3547096 accepted, connection dropped

2026-11-02: LS6 reconnected, queue empty, WORK 686,917 files. Clean git pull
reached registered commit 3fa39cc83b3eea080ef981226276ca9ace7c7501, matching
the Mac and origin. Reference job **3547096 accepted**, development/TRA25006,
one node, two-hour limit, at most 2 SUs. Last verified PENDING, no start/end.
Do not pull LS6 while it is pending or running. No normal job was submitted.

The next status check lost the master connection (Broken pipe) and returned
Permission denied plus password/MFA instructions. Stopped remote access; no
authentication, retry or duplicate submission. The user must reconnect again.
New checkpoint and exact verification/resume steps:
`notes/s2_reference_2026-11-02_v1/STATUS.md`; accepted receipt in
`submission_v1.json`. No reference outcome is yet verified. E follows reference
completion; E2 and paper edits stay held.

## Latest checkpoint — reference packet frozen, SSH blocked, 2026-11-02

The user reviewed S2 and authorized reference validation first, then E audit
and quota-interrupted resumption. F767 must be labeled an F4 configuration
replica in every derived table; that label is now explicit in the current
S2 report/CSVs without changing any outcome or count. Full-application versus
isolated results remain side by side, with phase supported but not measured.

The first BatchMode-only LS6 queue/quota check returned Permission denied with
password/MFA instructions. Remote access stopped immediately; no pull, build,
simulation, deletion, reference job or E job was submitted. The user must
reconnect personally and confirm before remote access resumes.

Meanwhile new task-specific reference sources, new outer adapters, and the
pre-execution DESIGN amendment were prepared locally. Protocol:
`notes/s2_reference_2026-11-02_v1/PROTOCOL.md`; sealed packet in its `packet/`.
Plan SHA-256 `ceb14326dea354408799e1e9a2356ee5c29dec4851998ad3fb56107798a3e7c7`;
code-manifest SHA-256 `c649855b2146b0fa46cc9ac18695f330f875af17e1893789cde49fc2be02acbd`.
Eleven new reference builds, 77 qualification launches, then 274 evaluation
launches covering all 470 primary failures. No reference has been built or run.

Planned job: development/TRA25006, one node, two-hour limit, at most 2 SUs;
four concurrent builds then 32 Launcher workers, with a qualification gate
before evaluation. It uses the original build/run body unchanged, new sources,
SCRATCH builds/records and node-local runtime. Kept ELFs/logs/configurations and
raw records are archived on WORK, with before/after protection audits and a
fresh headroom check before publishing. No normal reference submission is
authorized by the packet. A failing reference is flagged for firmware/simulator
investigation, not test brittleness. The seconds-rate contract is retained
alongside a separate legal-clock progress reference.

Next after reconnection: commit/push prepared code from the Mac; git pull only
on LS6 (3546149 is finished), verify HEAD/seals, inspect queue/headroom, and
submit the development reference job once. Reconcile any uncertain sbatch
acceptance rather than duplicating it. On reference completion transfer,
verify and update the per-failure table. Only then audit E's partial records,
register its exact infrastructure-interrupted retry list, and submit approved
chunks of at most three hours with reported SUs. E2 and paper edits stay held.

## Latest checkpoint — replay evidence verified and S2 report delivered, 2026-11-02

Job **3546149 COMPLETED 0:0**, elapsed **00:12:26**, scheduler start
2026-11-02T07:21:12 and end 2026-11-02T07:33:38. No LS6 pull or new job
submission occurred during this continuation. The watcher remains paused.

The returned WORK archive has SHA-256
`9247f19e878b94370e8d9ed85717dfacc787184654ab90f68d661ff1bb56dfb2`.
Independent local verification checked its checksum, complete-state receipt,
2,214 manifest entries, safe extraction and exact extracted inventory.
Protected-before and protected-after each match all 30,067 baseline hashes.
`compare_replays.py` reports **274/274 identical replays**, covering **470/470
case failures**: no verdict, UART, trace, selected-field, provenance or roster
differences; zero missing replays. No primary verdict was replaced.

The source-supported S2 report and machine-readable case/application,
frequency-band, category, source-excerpt and isolated-case reconciliation
tables are in `notes/s2_attribution_2026-10-31/s2_report_20261102_v3/`.
Observed flip cases: F4 6/10 runnable, F767 6/10, F746 4/6, H753 0/10
runnable at any setting (0/9 nominal runnable). Missing slots: zero.
Category case counts (a/b/c/d) per board: F4 1/3/1/1, F767 1/3/1/1,
F746 1/2/0/1, H753 0/0/0/0. Cascades are not independent waiting defects.
Counter all-channels uses category (b)'s free-running relative-tick phase
subtype, explicitly distinct from calendar-write phase.

Platform input hashes confirm all four boards use STM32F4_RTC. Full-app
versus isolated F4 seeded failures are pending 26/26, callback 22/26, and
counting 12/17; the last two have four and five isolated-fail/full-pass
settings, with none in the reverse direction. Preserved model phase supports
the context explanation, but phase was not directly observed. H753's extra
runnable case passes its timing-based capability gate in 10 seed settings;
90 seed skips plus both endpoint skips remain skips, not passes. The gate's
exact internal false-return branch is not logged.

**References have not run.** Categories are post-result source-supported
explanations, not reference-validated brittle-test counts. S2 evidence and
replay results are ready for Progress Report 2 without waiting for E.
Reference protocol registration/approval, E, E2 and manuscript edits remain
held. User edits to main.tex and main.pdf are not staged or committed.

## Earlier checkpoint — S2 replays submitted, 2026-11-01 (superseded)

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
