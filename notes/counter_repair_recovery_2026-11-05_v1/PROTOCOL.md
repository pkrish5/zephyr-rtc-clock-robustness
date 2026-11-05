# Counter-repair infrastructure audit, 2026-11-05

This is a read-only development-queue audit before proposing recovery. Original
jobs 3552460–3552463, their input bundle, source variants, forecasts, records,
and harness remain unchanged. No original job is canceled or resubmitted here.
No Renode simulation, test build, scientific setting, or manuscript is changed.

Verified status: build 3552460 completed 0:0 on c304-021. Nominal gate 3552461
failed 127:0 after two seconds on c314-191, reporting missing Lmod paths and
`apptainer: command not found`. Legal 3552462 and fault 3552463 remain pending.
The login node currently has readable Lmod files. A compute-node mount problem
is a possibility, not an established root cause.

Run one development/TRA25006 job, one node, 15-minute limit, reservation and
estimated ceiling 0.25 SU. It checks pinned tacc-apptainer/1.4.1 and launcher/3.10
using the existing storage runtime, hashes the calibrated v10 SIF, performs only
`apptainer exec ... /bin/true`, and records node/module/path availability.
All loose outputs and temporary/cache files use SCRATCH or node-local /tmp.
The existing packed-output wrapper checks WORK headroom and all 30,067 original
protected files before/after, then publishes a verified WORK archive. No prune.

Verify the unchanged original counter plan
`c5d2f7f515a59f2d45bcad665ab649b251051904704a1c96186610d08141ea8d`,
all its input/code hashes, and the 764-file active remote counter seal captured
before the repeatability study. The separate 20-file Mac source/document seal
is checked locally; those Mac-only documents were not runtime inputs on LS6.
Check every saved build record, ELF, build log, recorded
configuration/devicetree hash, compiled case list, and process exit. Keep copies
of those artifacts, original source variants, configs, and original Slurm logs
in this new archive, together with the active runtime input files. Intermediates
are not selected and are not deleted. A byte-identical copy of the original
scientific protocol is carried in this new namespace; the original is not edited.

Pre-execution packaging correction, 2026-11-05: the first read-only pre-pull
check incorrectly treated all Mac-only documents as LS6 files. It encountered
the absent HANDOFF.md, not a measured digest mismatch. No job was submitted.
The new diagnostic now distinguishes the 764-file active remote seal (from the
unchanged repeatability packet) and 20-file Mac seal. All original seals and
scientific inputs remain unchanged. This revision predates any diagnostic run.

Inventory any existing primary records and stage process files. Record the
actual indices and hashes; do not assume zero nominal launches from the job
exit alone. A failed/missing hash or unexpected record stops recovery planning.
Retain all old bytes and missing outcomes. Full build validation is independent
of Slurm's completed state.

After returning and independently verifying the packed audit, prepare a separate
engineering amendment/plan in fresh output paths if a recovery is justified.
Do not change the sealed worker, tests, ELFs, task settings, deadlines, fault
operators, or outcome rules. Any new normal-queue job requires the user's
approval after its node count, wall limit, estimated SUs, and exact work are
reported. Do not run a replacement nominal gate or scientific task from this
audit. Keep the existing watcher paused and the manuscript unchanged.

Use bounded BatchMode SSH. Stop remote access on credentials, authentication
failure, dropped connection or stalled I/O. No automatic reconnect or blind
submission retry. Preserve each attempt/receipt and stop after three consecutive
infrastructure failures. The original gate is the first known failed attempt;
this development audit is diagnostic, not a hidden gate retry.
