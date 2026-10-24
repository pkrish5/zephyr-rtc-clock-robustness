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
