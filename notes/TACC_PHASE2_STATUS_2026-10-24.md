# Phase 2 status, 2026-10-24

## Authorization and immutable baseline

User approved A–B and then D on normal, allocation TRA25006. E is limited to
registration and review examples until a further approval; E2 is deferred.
Phase 3 must show a before/after number table before paper edits. The open
manuscript and PDF have pre-existing local changes and are untouched.

The restored authenticated LS6 session returned the expected WORK path. A
sandbox network denial was retried with the required network permission;
there was no authentication attempt or account change. All remote paths
remain under `$WORK/zephyr-rtc-clock-robustness`.

Protected baseline: 30,067 files, covering the previous protected set and
all final Phase 1 harness/packaging bytes. No packaging exemption in Phase 2.
Local baseline and full before/after audit are in
`artifacts/tacc_phase2_20261024_v1/protected_baseline.json` and
`pre_ab_hash_check.json`; the latter SHA-256 is
`5da05e76ed536e1b31dbc0e14b62d588ca2e5d8a7331e4a34e7c2b2d4fe6f70a`.
All 30,067 files were unchanged before A–B submission.

## A–B submitted

- Job **3532327**, normal, TRA25006, one node / 128 allocated CPU tasks.
- Whole-node Launcher 3.10, cap 32 processes, no Slurm array.
- 16 frozen forecast-only suites, 100 seeds and two endpoints each:
  **1,632 primary cases**. Every subject is calendar counting.
- Estimated 6,500.1 seconds = **1.81 SUs** at one SU/node-hour;
  requested 03:00:00, reservation ceiling **3 SUs**.
- Reuse calibrated SIF
  `94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
- Remote bundle: `tacc_work/20261024-phase2/ab-bundle`.
- New result prefix: `results/tacc_phase2_ab_20261024_v1` inside that bundle.
- Before execution, scripts and amendments were committed as `ce03de38`,
  pushed locally, then pulled on LS6 with `git pull --ff-only`.
- Submission returned a definite job ID. Latest queue read: PENDING,
  Priority. No result is claimed yet.

The new adapter calls the unchanged calibrated simulation function, reuses
saved platform bytes, and enriches only new records with execution provenance.
Raw forecast files are read-only and sealed. Harness outcomes remain missing;
there is no retry-until-pass path. Explicit assertion failures receive a
fresh-process replay and a frozen reference per distinct failing frequency.

## D prepared, not submitted yet

The prior-to-execution DESIGN amendment specifies 207 primary plus nine
reference controls, 216 total build/run attempts, across three distinct
disabled implementations. The oscillator zero control uses the production
driver at nominal frequency; the nonarrival zero control explicitly disables
all QUALITY switches; the offset zero control uses sign zero. Both signs
share one disabled implementation. New control ELFs are separate from old ELFs.

Cap 16 workers with two compiler workers each and 4 GiB allowance per worker.
Provisional estimate: 6,071.4 seconds = **1.69 SUs**; request four hours,
reservation ceiling **4 SUs**. Build allowance is not a measured build rate.
Submit after A–B, or with an `afterok` dependency ensuring that execution order.

## Outstanding checkpoints

- Collect A–B verdicts, exact forecast comparisons, replay/reference results,
  resource usage and protected-file post-audit.
- Execute and report D, keeping build failures, test failures and missingness
  distinct, and references separate.
- Register E and present six source diffs. No E builds/runs or E2 generation.
- Stop before repair execution and before paper updates.


## D submitted with enforced ordering

Job **3532338**, normal / TRA25006, one node, 04:00:00, cap 16,
`afterok:3532327`. D cannot start unless A–B exits successfully. Estimated
**1.69 SUs**, reservation ceiling **4 SUs**. A–B estimate remains 1.81 SUs,
reservation ceiling 3 SUs. These use the normal charge of 1 SU/node-hour;
TACC's 15-minute minimum applies if a job exits early. Verified source:
https://docs.tacc.utexas.edu/include/lonestar6-jobaccounting/ and
https://docs.tacc.utexas.edu/hpc/lonestar6/ (accessed 2026-10-24).
D scripts were pushed locally in `76bcd297` and pulled on LS6. Neither A–B's
sealed code nor its inputs changed when D-only files were added.

A–B plan SHA-256: `3803eb093e3c4348cc477b2b9562d68259a8891881d059dee790fc68607331c8`.
D plan SHA-256: `0b846ab53dea9c318d8493664e406822f5585a59173848403f3736f827e99898`.
Latest queue check: A–B PENDING (Priority), D PENDING (Dependency).
No new experimental verdicts have been read at this checkpoint.

## E registered and review-only examples prepared

The dated amendment was appended to DESIGN before any example source was
created. Exact amendment text and SHA seal, 33-subject source/ELF roster,
six V0-to-variant diffs and six preview C files are in
`notes/repair_review_2026-10-24/`. The manifest marks every example
`REVIEW_ONLY_NOT_BUILT_OR_RUN`. A balanced-parenthesis assertion extraction
confirms every original assertion invocation is retained in every preview.
No E build, run, or E2 model call occurred.

Important approval choice: the requested 18.824 + 2 second deadline is
20.824 seconds exactly. V1 normalizes longer original budgets down to this
ceiling, rather than merely extending short waits. V2 uses protected event or
state observations with 20-ms polling, and may be only a cadence change for
already polling subjects. V3 adds only required task checks; it does not add
an exact upper calendar bound to the pending task's looser specification.

Wait for explicit approval before generating the full E cohort or executing
any E variant. Review D outcomes before any such execution. No manuscript
or original analysis count is updated in this phase.


## 2026-10-24 approved V1/V1b split and E preparation

User approved E execution with V1=max(original,20.824 s), a separate V1b
exactly 20.824 s, and unchanged V2/V3 semantics. The dated DESIGN revision
and service-stage clarification were written before any repair builds/runs.
The updated six diffs include an over-padded 60-second counting suite:
V1 is a deliberate no-op; V1b reduces its scalar ceiling. The full cohort
contains 165 source versions, with 22 V1 source/ELF no-ops. Source sites were
sealed first. All non-time assertions remain unchanged; the two timeout-only
assertion substitutions are enumerated in the source manifest. The old V2/V3
example sources are byte-identical. E2 remains on hold.

Offline policy tests pass: infrastructure/ambiguous nominal outcomes cannot
clear the five-run gate, V1 never shortens a recorded scalar budget, and the
approved V2/V3 examples are unchanged. Python/shell syntax checks pass.
These are adapter checks, not new firmware experiments.

E bundle plan SHA-256:
`2c9317ea293b72a4cbf1e7779f22ceecdbf5f3a835559db35e4114a1a95971b6`.
The sealed inputs include original source/ELF bytes, new mechanical source
copies, immutable fault drivers, saved legal/nominal/fault platform files,
references, overlays, configurations and the unchanged original simulation
code hashes. No E build or run has occurred at this checkpoint.

E submission plan: gates/builds one node normal four hours, estimated 2 SUs;
controls/evaluation one node normal 18 hours, estimated 8 SUs. Total estimate
10 SUs, reservation ceiling 22 SUs, with D then gate-job dependencies and
explicit compute-node D verification. Details and exact commands are in
notes/repair_revision_2026-10-24/EXECUTION.md. These are planning estimates;
no E job has been submitted while the connection is unavailable.

## A–B completed; connection stalled during return transfer

Job 3532327 COMPLETED, exit 0:0, 00:32:35, node c314-024. The compute-generated
report records 1,632/1,632 passes (16 suites x 102), 1,600/1,600 exact seeded
forecast matches, zero mismatches and zero missing verdicts. It verified raw
record/traces on the compute node. At one SU per node-hour the elapsed charge
estimate is 0.543 SUs. New endpoint outcomes remain separate from forecasts.
No assertion failure required replay or a failing-frequency reference.

Returned report SHA-256:
`20b9abe19a83b2bd2867c856443072303d7541151f36c8b4713078c741a02749`.
The rsync transfer stalled before the bulk raw record/trace directories
arrived, so independent local raw-hash verification is still pending. The
returned report alone is not described as a complete local artifact return.
The protected-file audit still finds all 30,067 original protected files
unchanged: pre_e_source_hash_check.json, SHA-256
`fa9dc7612bd2244306e197ab50b8412112a7feb2cb489c83b876538dcfd69d0b`.

The next status SSH client stalled for over a minute, and the rsync client
for over three minutes. Stopped only those local clients (PIDs 1421, 1422,
1555); did not stop Slurm jobs or touch the authenticated master connection.
No authentication attempt was made. Asked user to restore/check the session
and confirm resumption. Latest confirmed D state was PENDING (Priority).
Remote monitoring, transfer and E submissions are paused for connection
recovery. Local protocol/adapter preparation continued. No paper edits.


## 2026-10-24 resumed access and first E submission

User confirmed reconnection. The read-only check succeeded; D was still
PENDING (Priority). Pulled the approved scripts on LS6 with git pull only,
transferred a path-validated 9,991,877-byte bundle archive, and unpacked it
inside the new WORK repair directory. Remote plan SHA-256 matched the sealed
local value 2c9317ea293b72a4cbf1e7779f22ceecdbf5f3a835559db35e4114a1a95971b6.

E gates/builds submission returned definite job **3532458**, normal,
TRA25006, one node, four-hour limit, cap 16, afterok:3532338. Estimate 2 SUs,
reservation ceiling 4 SUs. Compute preflight additionally requires all 216 D
builds and nominal controls to pass before any repair compilation starts.
Local receipt is artifacts/tacc_phase2_20261024_v1/e_gate_submission.json.
All 30,067 protected files remain unchanged at submission; full audit
SHA-256 5ec82c4a4f7e95633c9419ec579cffbff2cbbc690210e58e893921e235a7bdcc.

The dependent E evaluation submission (one node, 18 hours, estimate 8 SUs)
timed out before returning a job ID. Its acceptance is UNKNOWN; do not
resubmit until a read-only scheduler check resolves the original attempt.
The concurrent A–B rsync was still making partial progress, so no credential
expiry is inferred. Paused only the transfer client and issued one bounded,
read-only queue check. No authentication attempt or account change.


## E evaluation acceptance resolved without duplicate submission

The one read-only scheduler check returned successfully and confirmed
**3532464 | rtc-repair-eval | PENDING | afterok:3532458(unfulfilled)**.
The timed-out submission had been accepted. No duplicate was submitted.
No credential expiry/drop is inferred: the shared transfer was progressing,
and the bounded follow-up read succeeded after pausing it. The original
unknown-outcome record is retained, alongside the resolved submission receipt.

Approved job chain is now:
D controls 3532338 -> E builds/gates 3532458 -> E evaluation 3532464.
All three were pending at the last read. E gates use one node / 04:00:00,
estimate 2 SUs; E evaluation uses one node / 18:00:00, estimate 8 SUs.
Normal / TRA25006 throughout. Total E estimate 10 SUs; reservation ceiling
22 SUs. D's explicit raw-hash/pass checks and E's reference controls remain
mandatory before downstream execution. No further scientific approval is
needed to execute this approved chain. E2 and paper edits remain held.

A–B raw return is partial (claims transferred, bulk records/traces not yet
returned). The compute-verified report is present locally; no claim of full
local raw verification is made. The per-file rsync was paused to avoid
blocking status/submission traffic on the shared connection. Complete raw
artifact return and independent verification remain required before the
Phase 3 before/after report. No E outcome has been observed yet.


## 2026-10-24 Phase 2 compiler-cache infrastructure correction, before E builds

D job 3532338 encountered a common build-environment failure: pinned Zephyr
attempted writes beneath `/opt/zephyrproject/zephyr/.cache` inside the read-only
SIF. Two independently inspected initial build logs show this same compiler
capability-cache error. These are infrastructure build losses, not selected
ztest assertion failures or evidence against a source. The attempt was
cancelled and its existing logs/build records remain preserved in D v1.
Unstarted E jobs 3532458 and 3532464 were cancelled before any repair build/run.
Do not substitute successful retries into those original failed records.

Under the standing infrastructure-only development-queue authorization,
validate a path-only fix in a new D v2 bundle/results directory. Set explicit
container XDG_CACHE_HOME=/var/tmp using APPTAINERENV_XDG_CACHE_HOME; /var/tmp is
already bound to a private per-task runtime/work directory under WORK.
Pinned `cmake/modules/user_cache.cmake` prefers this writable cache location.
No SIF rebuild, firmware source change, driver modification, compiler flag
change, frozen ELF change, forecast change, or simulation-loop change.
Both the original D Python worker and original E build/simulation adapters
remain byte-identical; new shell packaging wrappers only set the cache path
and allow development execution for the D retry.

D v2 keeps the exact 216-task roster, source/config/driver hashes and frozen
simulation hashes. Its new plan SHA-256 is
61b8715bce7400dc5a380599731f970d8657defb946584875973cdfde81e6518.
Run task 0 once, confirm its successful build and nominal pass, then pack
only tasks 1..215. If that first control fails, stop before launching the
remainder. Report the actual development partition in every record. Source
and raw-result immutability checks precede and follow the fix; count the
cancelled D job as infrastructure attempt 1. Stop after three consecutive
failed infrastructure attempts; any required simulation/test-input change
still requires separate approval. After complete passing D controls, restore
the already-approved E normal jobs with the same scientific plan and sealed
source cohort, using the validated cache environment. E2 stays held and
Phase 3 must precede any paper edits.


## D cache retry submitted on development

Job **3532515**, development / TRA25006, one node, two-hour limit, cap 16.
Provisional estimate 1.69 SUs, reservation ceiling 2 SUs. This is infrastructure
attempt 2 after the cancelled read-only-cache attempt; task 0 must build and
pass before the remaining 215 controls launch. New D v2 plan hash matched on
LS6; the original D/E worker code and input hashes remain unchanged. Receipt:
`artifacts/tacc_phase2_20261024_v1/d_cache_v2_submission.json`. E remains
unstarted and cancelled pending validation. The A–B read-only packing job
3532492 reached COMPLETING; archive return and local verification are next.

The D v2 first-control gate succeeded: the development stdout entered Launcher
for tasks 1..215 only after task 0 built and passed. Thus the writable-cache
fix passed its first planned control; full D outcomes remain pending. A bounded
read-only SSH check succeeded after pausing the stalled rsync client; there
is no evidence of credential expiry. Protected-file post-submission audit:
30,067 unchanged, SHA-256
24e6dc335f4f647b99c71532994459a2b8812875a15abef14bed8e0b30e5da40.


## A–B complete raw return and independent local verification

The read-only compute packaging job 3532492 completed. A single compressed
rsync transfer succeeded after earlier uncompressed attempts stalled. Measured
throughput was approximately 6 KB/s; authenticated read-only SSH still worked
after pausing transfer traffic, so no account change or authentication retry
was performed. Archive SHA-256:
1704dc2bc2f2b71f7d2fdb6c49319469704603a895defaaf3253f03585fd40ea.

All 13,070 archive members were checked for relative paths, regular files or
directories only, then extracted into a new local complete-return directory.
The original report adapter independently rehashed returned trace/UART/monitor
files and checked required provenance. Its result exactly equals the compute
report: 1,632/1,632 passes, 1,600/1,600 seeded forecast matches, zero
mismatches and missing verdicts. Source: returned-ab-complete/local-verification.json
under artifacts/tacc_phase2_20261024_v1. Partial earlier transfer directories
and original frozen results remain intact. No manuscript counts were edited.

Latest D v2 progress: 3532515 RUNNING on c307-005, elapsed 10:02, 83 build
records and 82 nominal records present. No STOP marker was reported. These
are progress counts only, not a final control result. E has not started.


## A–B derived comparison prepared for later Phase 3 review

New read-only adapter `harness/tacc_phase2/compare_ab.py` verifies all old
suite summaries against their original seeded records; checks all new raw
output hashes, original source/ELF hashes and schedule; and verifies the
existing mutant-record hashes before calculating combined yields. It writes
only a new derived file, never the frozen analysis ledgers.

`returned-ab-complete/ab-derived-comparison.json` records source-file hashes
and before/after values: measured suites 50 -> 66; forecast-only 16 -> 0;
seed slots 5,000 -> 6,600; passing seeds 4,951 -> 6,551; assertion failures
37 -> 37; harness errors 12 -> 12; confirmed robust attempts 39 -> 55;
robust plus slow/nonarrival detections 29 -> 38; stricter non-padding Q
5 -> 14; evaluated predictable suites 14 -> 30 and exact verdict matches
1,400/1,400 -> 3,000/3,000. These are A–B-only derived values for the
Phase 3 review, not manuscript changes; D and E remain pending.

At elapsed 11:39, D v2 had 101 build and 99 nominal records, no STOP marker.
No E source generation, compilation or execution has started.
