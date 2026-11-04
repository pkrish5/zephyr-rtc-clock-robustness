# Approved path-only repeatability recovery, 2026-11-04

Registered before recovery execution. The user approved recovery and a combined
4.0-SU ceiling, including the two failed preflight attempts. This is an
infrastructure path correction to the same scientific study, not new subjects,
new settings, a broad rerun, or replacement of any observed verdict.

The archived jobs3552681/3552682 stopped at the SIF hash gate before Launcher,
Renode or any primary evaluation. Their independently verified archives contain
zero launched indices and zero verdicts. Keep both archives and all old intent/
receipt files unchanged. All180originally scheduled indices remain not started.
No finalized missing outcome is replaced.

Use the unchanged original packet at
notes/fixed_repeatability_2026-11-04_v1/packet/plan.json, SHA256
9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613.
Its scientific protocol SHA256 is
8871169a60dbb37b3be2aa52d668b5a5ba609a35aca8c16b5ca5b7c63ccd7da2.
All6cells,30fresh processes per cell, archived F4 full-application ELFs,
frequencies, source, Renode/SIF hash, CPU/SysTick, quantum, observation step,
per-task limits, outcome definitions and missingness rules remain identical.
No execution worker or frozen simulation logic is changed.

The only execution-environment correction is selecting the existing intended
physical SIF at tacc_work/20261023-v10/images/rtc-ls6-v1.sif, whose expected
hash94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
already appears in the original plan. A new receipt-protected submit.py adds
readability/sidecar/image.json checks. The full actual SIF hash is still checked
on a compute node before any process; no hash guard is weakened or bypassed.

Use new WORK metadata tacc_work/20261104-fixed-repeatability-v2 and new SCRATCH
Slurm-log namespace fixed-repeatability-20261104-v2. Loose runtime remains
job-specific SCRATCH/node-local,tmp; verified packed WORK archives have fresh
job IDs. The two new jobs depend only on each other (counter afterany RTC),
never on counter-repair3552460-3552463. Do not touch those four jobs or their
sealed inputs; verify active execution-code hashes before/after code pull and
all active input hashes in the unchanged coordinator before/after execution.
No git clean, pruning, code editing on LS6, or paper edits.

Fresh development/TRA25006 cost: RTC90launches, one node32workers,1.5h ceiling,
estimate0.727864SU; counter90launches, one node32workers,2h ceiling,
estimate1.714042SU. Fresh estimated total2.441906SU; fresh reservation3.5SU.
The failed short jobs imply0.5SU under the0.25node-hour/job minimum (accounting
not independently confirmed), yielding estimated combined2.941906SU and approved
combined ceiling4.0SU. Do not reduce timeouts/repeats to hide infrastructure cost.
No normal-queue repeatability submission is authorized.

Report all pass/fail/skip/missing counts per cell after independent archive and
record verification. No scientific outcome exists from the failed attempts.
If another input/hash gate fails, preserve it and stop; no blind resubmission.
All30agree means no observed same-setting flakiness, not exclusion of rare
flakiness. Timelines continue to distinguish measured UART/kernel durations,
sampled Renode exposure and source inference. The separate counter-repair
follow-up and paper-update gates remain unchanged.
