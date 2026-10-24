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
