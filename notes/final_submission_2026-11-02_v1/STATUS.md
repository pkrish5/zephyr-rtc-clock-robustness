# COMPLETE: submission release published and public downloads verified, 2026-11-03

Release: https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/tag/course-submission-2026-11-03-v1
Published 2026-11-03 12:53:22 CST (18:53:22 UTC), release ID 433093947.
Immutable submission tag still points to 67ecb3d90e93895d5c5073ca6e8b78e9c8d1a05d.
The human completed browser sign-in; the existing tag was selected and the
four approved files uploaded and published: evidence archive, SHA sidecar,
exact-tag fresh-clone proof, and main.pdf. No account/SSH settings were changed.

Anonymous public downloads of PDF/checksum/clone proof match local hashes.
The public archive URL then passed make tables without a cached archive or
GitHub credentials: 113,433 files verified, eight table fragments exactly match,
zero Renode runs, 61.713 seconds using Python 3.12.14. The prior fresh GitHub
clone test on Python 3.14.6 remains PASS/clean at 35.098 seconds. Public release
metadata, all digests, download receipts and output are in published_downloads_v2/.
Screenshot: release_published_v1.png. PDF remains five total pages, 23 resolved
inline references, zero [?]/undefined diagnostics and zero overfull h/v boxes.

Two validation-environment details are disclosed, not hidden: the system Python
3.14 lacked a configured trusted CA store, so the public test used bundled
Python with its trusted certifi roots and TLS checks enabled. The second Python
runtime changes a full-precision normal-CDF sensitivity CSV checksum by last-bit
rounding (examples around 1e-17); only the derived provenance manifest differs,
while all eight manuscript table hashes and all raw evidence remain identical.
The initially stricter clean-status wrapper assertion was investigated and the
actual provenance difference recorded; no raw result or table was modified to
hide it. DATA.md explains this cross-runtime detail. No extra experiment ran.

Phases A–D are complete. Keep the watcher PAUSED; no TACC monitoring/jobs,
collector/recovery resubmission, E2, new experiment, prune or tag replacement
is required. Later documentation-only commits retain the immutable submission
tag. No further authentication is needed for public download/reproduction.

# Exact submission tag verified; watcher PAUSED for release upload, 2026-11-03

Submission tag course-submission-2026-11-03-v1 is pushed at immutable commit
67ecb3d90e93895d5c5073ca6e8b78e9c8d1a05d. A second fresh GitHub clone of this
exact tag passed make tables with the documented cached evidence archive:
113,433 files verified, eight matching table hashes, zero Renode runs, 35.098 s.
Tracked clone files stayed clean. See clean_clone_exact_tag_v1.json/.txt. The
five-page PDF, 23 resolved inline references and zero overfull/undefined checks
remain verified. All experiments and local artifact work are complete.

GitHub release upload is NOT complete. Git SSH works, but the browser is signed
out, the configured HTTPS helper has no credential, and the Mac is locked for
native UI access. The human sign-in request is pending. The automation is
confirmed PAUSED with failed-runs-only notifications and this checkpoint in its
saved prompt. No automatic authentication/retry is allowed. No TACC job or poll,
E2, new experiment, frozen-input edit, prune or tag replacement is needed.

On human GitHub sign-in/gh authentication, publish the existing verified archive,
SHA sidecar, exact-tag clone receipt and PDF using reproduction/publish_release.sh
(or the authorized signed-in browser), then verify the release/download hash and
report its real URL. A cached-archive test is not a public download test; do not
claim the latter until it runs. Release assets are retained in submission_assets/.
The submission tag remains on 67ecb3d9; later status-only commits do not alter it.

# Phases A–C and local D complete; GitHub release sign-in required, 2026-11-03

Final candidate a82148aeba825eb052ada67934861dcecbf56d06 was pushed and cloned
fresh from GitHub. The documented cached-archive make-tables command PASSed:
113,433 evidence files verified, all eight table hashes identical, 0 Renode
runs, 46.061 seconds; tracked clone files stayed clean. See
clean_clone_test_v1.json/.txt. Network asset download is not yet tested because
the release asset has not been uploaded. DATA.md, machine file/field catalogue,
raw S2 checks and the complete Phase 3 package are committed. All 30,067 original
protected files pass the final local audit. No old missing outcome was replaced.

The same-source paper is five total pages, 23 visible/resolved inline references,
zero [?], zero undefined diagnostics and zero overfull h/v boxes. Built-in editor
compilation succeeds; final exported PDF and all five rendered pages were checked.
No further TACC checks/jobs, E2, experiments or pruning are needed or authorized.

Remaining action is GitHub release publication of the verified archive and PDF.
Git SSH push works, but no configured HTTPS credential is available; the app
browser shows GitHub Sign in, and native UI access reports the Mac locked.
Do not authenticate on the human's behalf or expose credentials. A sign-in
request is pending. Finish the non-overwriting tag/final clone validation, then
pause the watcher at this actual authentication blocker. On human GitHub sign-in,
resume only the release upload, verify the published asset/download and final
links, deliver, and keep the watcher paused. Do not redo experiments/collector.
Local release assets remain under submission_assets/ (ignored by Git), including
the verified archive, SHA sidecar, release notes and exact publication command.

# Phase C complete; Phase D reproducibility in progress, 2026-11-03

The existing manuscript is revised from independently reconciled evidence and
compiles successfully with the built-in editor. The exported same-source PDF
was rebuilt with Tectonic 0.17.0 and visually inspected on all five pages: 23
inline references, no unresolved citations/references, zero overfull h/v boxes.
All eight table fragments are generated; the stronger S2 raw audit checks all
1,122 primary launches, 274 replays and 470 failure-reference links, without
changing any scientific values. Phase A/B gate remains passed.

Phase D has a new exact 113,433-file evidence archive, read back and hash-verified
(SHA256 805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921).
DATA.md and a safe no-Renode make-tables command are prepared; fresh-clone test,
final push/tag/release remain. Git SSH can be used for publication; no GitHub
HTTPS credential was available, and the browser is signed out. Release upload
may require human GitHub sign-in after all independent work is complete.
No TACC job, experiment, E2 or prune was performed in this continuation.

# RESUMED: Phase A/B evidence gate passed; Phase C authorized, 2026-11-03

The human confirmed MFA reconnection and requested resume. BatchMode check
succeeded: collector 3549010 COMPLETED 0:0 in 5:38. Archive returned and verified
exactly (39,958 entries; all protected hashes unchanged); archive SHA256
77abe35e33eec8972ea758fc1277dbac5a178cdf5788897381b9eb25dbb5722c.
The collector copied/rehashed 38,000 files without simulation, build or deletion.
No resubmission occurred. Earlier authentication/tool blockers are resolved.

Offline reconciliation and the complete Phase 3 package are saved under
phase3_package_v1/. All 17,375 primary indices reconcile: 16,888 pass, 458 fail,
29 finalized missing outcomes retained. All 458 failure replays match persisted
fields and raw trace bytes; all 112 legal-failure reference links pass. A second
raw-record recount/hash/duration check agrees. Core RTC cohort retains original
12 missing slots: contrast 3/34 vs 0/32, Fisher171/715 (p0.2391608392), robust55/90,
optimistic ceiling63/90, robust+slow/nonarrival38/90, descriptive Q14/90.
Full before/after ledger and S2 references/examples/sensitivity/two-axis tables
are in the package. See phase_AB_internal_review_v1.json for the internal review.

Proceed directly to authorized C then D, without a Phase 3 human stop. Keep
S2 failed rate references unresolved, F767 a configuration replica, phase
explanation supported not measured, and S2 slow faults not measured. No more
TACC jobs are required for this evidence package. Preserve author edits and
edit existing main.tex in place only; use built-in compilation and six total
pages. Re-enable the existing watcher with this authoritative checkpoint for
continuation if the active run yields. E2 and new experiments remain held.

# STOP: LS6 authentication expired; watcher PAUSED, 2026-11-03 10:12 wakeup

App permission review is working again: the purpose-built automation pause
request succeeded and saved status is PAUSED. The earlier tool-review timeout
is resolved. One authorized bounded BatchMode status command then actually ran
and LS6 returned exit 255, Permission denied (publickey,keyboard-interactive),
with TACC password/token instructions. Remote access stopped immediately; no
authentication, retry, resubmission, pull or job modification followed.

Human MFA reconnection and explicit resume are required by the standing rule.
Collector 3549010 already exists and must never be duplicated; current job
state remains unknown. After human reconnection, check that existing job, read
its logs if failed or return/verify its packed archive if complete, then continue
verified A/B/C/D under the existing authorization. All seven E recovery chunks
remain verified, and all old finalized missing verdicts remain missing. No paper
edits or Phase B execution occurred; draft/PDF hashes match their baseline.
Receipts: auth_blocked_20261103_1612_v1.json; previous tool-timeout history is
retained below, superseded by this actual authentication blocker. Keep the
watcher paused until the human confirms reconnection; preserve its full prompt.

# STOP: tool permission review unavailable, 2026-11-03

No further remote requests are authorized from an automatic wake while this
blocker remains. The existing collector 3549010 was last verified PENDING at
submission; its current state is unknown. No job failure or authentication
failure has been established. Do not resubmit it.

The status action timed out in automatic permission approval review before
process creation. Its one permitted retry yielded no result and was terminated.
Two attempts to pause this automation via the app tool also returned the same
permission-review deadline error. The saved automation is still ACTIVE; human
manual pause or restored tool approval is required. Do not bypass review by
editing automation.toml. No more retries in this run. The full A–D prompt is
retained for later resume. Local notes are saved but not committed/pushed because
escalated operations are unavailable. Draft/PDF hashes match their baseline.
See monitor_blocked_20261103_1405_v1.json. Resume only after this tool-access
blocker is resolved, then one bounded BatchMode collector status check.

# Monitoring blocked, 2026-11-03 08:05 America/Chicago wakeup

Collector 3549010 current state is UNVERIFIED. The first authorized BatchMode
status check was rejected before process creation because automatic permission
approval review did not finish before its deadline. The tool expressly allowed
one retry; that retry returned no result and its orchestration cell was
terminated. No further remote command was attempted. A local process-inventory
check was denied by the process sandbox, so execution of the retry is not
confirmed. Do not infer an SSH authentication failure or job failure.

Automation pause was requested but the app tool also returned an automatic
permission-review timeout, so PAUSED is not confirmed. Do not issue a fresh
remote request from a later wake until the access blocker has been resolved.
Its full A–D prompt must be retained. No jobs were
submitted/cancelled, no LS6 pull, no paper edit and no Phase B execution.
The accepted development collector must NOT be duplicated. Resume with one
bounded BatchMode sacct check only after this tool-access blocker is resolved;
if complete, return/verify its packed archive and continue the approved workflow.
Receipt: monitor_blocked_20261103_1405_v1.json. Do not ask for a password or token.

# Latest checkpoint: development collector 3549010 accepted, 2026-11-03

The original-E read-only collector was accepted as job 3549010, development,
TRA25006, one node, 02:00:00 limit, 2-SU reservation ceiling. One initial check
shows PENDING, 0:00 elapsed. Do not submit it again. Receipt:
original_e_submission_v1.json; initial status: original_e_initial_status_v1.json.
Its exclusive SCRATCH namespace is
/scratch/10970/pk23377/zephyr-rtc-clock-robustness/e-original-evidence-20261103-v1,
with collector-3549010.out/.err and submission.json. On completion, the WORK
packed-results stem is 3549010-e-original-evidence. Transfer four archive
sidecars/archive into a NEW directory, use the existing generic archive verifier,
then reconcile all original E bytes and primary indices before Phase B.

LS6 was fast-forwarded by git pull only after all seven sealed recovery jobs
finished. HEAD matched Mac/origin registration
2e8d7c43199b9d426f3d1d7dbcb04a15bac78ec9, with clean tracked status and empty
queue before submission. No remote code edit, normal submission, simulation,
build or pruning. Do not pull/mutate the collector's code while it runs.
The automation now checks 3549010 first and explicitly forbids duplicate
collector/recovery submission. Keep existing missing verdicts missing; proceed
through verified B then authorized C/D automatically when evidence is ready.

# Latest checkpoint, 2026-11-03 07:35 America/Chicago

The final E chunk 3547931 completed 0:0 in 24:50. Its archive (7,977 entries)
and extracted contents match exactly; all 978 indices validated: 961 pass,
17 fail, zero missing. All 17 failure replays match persisted fields/raw trace.
All seven chunks: 9,551 indices, 9,339 pass, 212 fail, zero new missing,
212/212 exact replays and passing references at all 26 legal failure slots.
All 30,067 protected hashes and 35,708 old evidence hashes passed each job.
Original plus recovery accounting covers all 17,375 indices; original 29
finalized harness errors remain missing. Final repair analysis is not done yet.
Archive SHA256: dae4b7eacafc931716eaf788001c364e863df8ea2824f7bf10ada69c5d54586e.

The sealed jobs have all finished, so the prohibition on LS6 pulls is now
satisfied. A read-only check found LS6 HEAD still f25ac1b65a793d24bef792c14a13c87062026ad3,
no tracked changes, and an empty user queue. Register the original-evidence
collector in DESIGN before submission, commit/push Mac, pull LS6 and verify
clean matching HEAD. Collector is development/TRA25006, one node, two-hour
limit, 2-SU ceiling; no simulation/build/prune. Submit with the new one-shot
submit_original_e.py helper and never duplicate an uncertain receipt.
Phase B/C wait for that original-evidence archive and full reconciliation.
Draft/PDF unchanged. No normal job, E2 or new experiment has been submitted.

# Latest queue checkpoint, 2026-11-03 07:05 America/Chicago

The final E chunk / 3547931 is now RUNNING (3:40 elapsed; Slurm start
2026-11-03T07:01:43). Its running ExitCode 0:0 is not a final success. Earlier
six chunks are independently verified; 978 indices in the last chunk remain
unverified. No new archive was ready at this check. No LS6 pull, submissions,
scientific analysis or manuscript edits. Both draft files retain baseline hashes.
When the final archive completes, verify it before pulling code or submitting
the authorized development-only original-E collector. Then continue B/C/D with
no Phase 3 human approval stop. Receipt: queue_checkpoint_20261103_1305_v1.json.

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

# Latest queue checkpoint, 2026-11-03 03:35 America/Chicago

BatchMode status check succeeded. Chunk 5 / 3547930 is now RUNNING (23:24
elapsed; Slurm start 2026-11-03T03:11:50); chunk 6 / 3547931 remains PENDING.
A running 0:0 is not a completed verdict or a verified archive. No new completed
chunk is ready to return. The five-chunk evidence checkpoint remains 14,960 of
17,375 accounted for, with 2,415 outstanding and 29 original finalized harness
errors preserved. No job submission, LS6 pull, new analysis or manuscript edit.
Both manuscript files match their recorded baseline hashes. Wait for completed
archives before advancing evidence-gated Phase B; retain automatic C/D authority.
Receipt: queue_checkpoint_20261103_0935_v1.json.

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

# Latest queue checkpoint, 2026-11-03 00:04 America/Chicago

The scheduled BatchMode check succeeded. E chunk 4 (3547929) is now RUNNING
(23:33 elapsed, Slurm start 2026-11-02T23:41:13); 3547930 and 3547931 remain
PENDING. A running ExitCode 0:0 is not a final success. No new completed archive
was indicated, so evidence-gated Phase B and paper edits have not started.
No job submitted, no LS6 pull, no authentication action and no records changed.
The original-E collector was read through with its wrapper: it requires all
seven recovery jobs COMPLETED before copying/rehashing old evidence on compute.
The manuscript/PDF still match the saved pre-work hashes. Receipt:
queue_checkpoint_20261103_0604_v1.json. Next wake checks these existing jobs;
continue all ready steps after completion, with no Phase 3 human approval stop.

# Scope update, 2026-11-02: automatic completion authorized

The human has removed the Phase 3 human-review stop and authorized automatic
progress through paper revisions (C), artifact documentation/reproduction,
commit/push/tagged submission release (D), after evidence verification (A/B).
The evidence checkpoint remains mandatory, but no human reply is needed there.
This supersedes the earlier stop/held-paper wording below. E2, pruning, new
scientific experiments and normal-queue submissions from the automation remain
excluded. Authentication failures still stop remote access; never authenticate
or retry automatically. Preserve the author's current draft; do not reset it.
The 30-minute wakeup should continue every ready authorized step in each run.
Pause only on completion or an unresolved blocker requiring human action.

# Final submission checkpoint, 2026-11-02

## Automation authorization and stop

The human explicitly approved extending the existing 30-minute automation to
continue Phases A–B automatically: verify archives, run existing-data analyses
and commit results, then stop at the Phase 3 review package. The saved automation
`watch-s2-replay-3546149` was verified ACTIVE with this scope. Notifications
remain failed-runs-only; unchanged queue checks stay quiet.

Automation may not submit/resubmit/cancel normal jobs, edit the paper, start E2,
prune evidence or advance Phases C/D. If a normal recovery submission becomes
necessary, pause and report it for the main workflow. Stop remote access and
pause on any credential request, authentication failure, drop or stall.

## Verified state

The first four E recovery chunks (3547925–3547928) are independently verified:
5,700 complete indices, 144/144 exact failure replays, passing references at all
26 legal-clock failing slots, and no new finalized missing outcomes. Together
with original retained records, 13,524/17,375 evaluations are accounted for.
The 29 original finalized harness errors remain missing.

Last verified queue state: 3547929 pending Priority; 3547930 and 3547931 pending
Dependency. Do not git pull on LS6 while any sealed recovery job is pending or
running. The LS6 code seal remains f25ac1b65a793d24bef792c14a13c87062026ad3.
No new remote job, pull, cancellation or experiment occurred in preparation.

S2 reference validation is complete for all 470 failure slots. Reuse the
verified evidence, including 105 failed rate references labeled as unresolved
firmware/simulator/contract investigations, rather than test defects. F767
remains an F4 configuration replica; phase carryover is supported but not
directly measured. Do not infer unmeasured S2 slow-fault outcomes.

## Prepared continuation

The local standard-library package builder is
`analysis/final_submission_v1/build_package.py`. It gates on the complete E
archive union before executing Phase B. Syntax, mathematical edge cases and
the missing-evidence gate passed; real dataset analysis has not yet executed.
These new scripts require full validation against the returned raw data before
any derived result is reported.

The read-only original-E collector (`collect_original_e.py` and `.sbatch`) is
prepared but not submitted. After all sealed jobs finish, inspect it, add a
read-only infrastructure note if needed, commit/push Mac, pull LS6 and verify
matching clean HEAD, then submit the development compute-only collector. It
copies and verifies existing data only, uses new SCRATCH output and packed WORK
publication, and performs no simulation/build/prune. Verify its returned archive
before reconciling original and recovery records. Do not run heavy collection
or hashing on a login node.

Protected audit: 30,067 unchanged, zero differences. Manuscript/PDF match their
saved hashes and were neither edited nor staged. Full audit is local; compact
receipt records its hash. No scientific counts have been changed in the paper.

## Next actions

1. Check remaining three existing jobs once per scheduled wakeup, BatchMode only.
2. Verify any completed chunk using the existing archive and per-index checkers.
3. Once all seven finish, collect and verify original E evidence as above.
4. Validate/run the offline package builder into a new output directory.
5. Deliver the full Phase 3 package and PAUSE for human approval before paper edits.
