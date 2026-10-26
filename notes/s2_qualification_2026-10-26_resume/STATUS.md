# S2 approved continuation, 2026-10-26

## Registered and prepared

Commit cc42b98f records the reviewed exclusions in paper/DESIGN.md with direct
archive evidence. F746 counter configuration is unchanged; F072 is excluded
for no test output, and its unconfirmed divider observation is not a finding.
Both watchdogs are excluded for no reboot. F746 RTC/seconds remain candidates.

The exact fifteen missing calibration indices and prospective acceptance vectors
are sealed in artifacts/s2_qualification_20261026_resume_v1/bundle/plan.json,
SHA-256 2df1e0d4e31dd02b91d79978e16ed5fe18fe86186662b9e1e68507e989a2c03d.
No scientific input, source, ELF, frozen forecast or prior outcome is changed.
All 30,067 protected files pass the pre-submission audit.

The development QoS maximum is 02:00:00 (queried from qdevelopment). Planned
continuation: one node, fifteen Launcher workers, one setting per worker,
development /TRA25006, maximum two hours. Expected about0.5SU, ceiling2SU.
Individual worker ceilings remain <=1800seconds; no deadline extension.
No continuation or production job has been submitted as of this note.

E read-only status: 3532543 PENDING for Priority; not started, normal partition,
18-hour requested wall limit. No E operation or E2 start.

## Transfer and repository infrastructure problems, before any run

First rsync failed authentication (255); stopped until user restored MFA.
The restored session then returned rsync file-I/O exit11 before the new parent
existed. Created only the authorized WORK parent; the next rsync completed
all37 entries /2,097,340bytes. This was input transfer, not a firmware attempt.

The required git pull fetched cc42b98f but its merge/checkout failed with
'Interrupted system call' on loose objects and new files on WORK. A subsequent
read-only repository-status command returned old HEAD eedb8b1e then stalled.
Stopped only the local diagnostic SSH client, leaving the user's master session
and all Slurm jobs untouched. No reset, checkout, force update, deletion,
account/SSH-setting change, build or Renode execution was performed.
Further LS6 access is stopped pending user confirmation that WORK is responsive.
Do not assume this is an MFA problem or a scientific failure.

Local production preparation is guarded by a verified all-15-accepted report.
The normal-partition outer adapter calls the unchanged sealed simulation
function with actual normal metadata, not a spoofed development partition.
Original code stays unchanged. Source/config/ELF checks precede any production
launch; F7 cache packaging uses exact previously returned SVD bytes. It is not
activated without calibration acceptance. Python/shell syntax checks pass;
a synthetic unaccepted report is rejected before any output or experiment.

## WORK-responsive retry: checkout collisions, no submission

After the user confirmed WORK was responsive, git pull fetched abff0ced but
refused to merge: the interrupted earlier checkout left two tracked files
modified and26 newly added files untracked. A read-only comparison verified
all28 files byte-identical to origin/main, including DESIGN.md, the status
note, continuation scripts and copied S2 evidence. HEAD remains eedb8b1e.
No recovery mutation, experiment or job submission has occurred.

The user's git-pull-only rule requires an explicit one-time recovery exception.
Prepared recover_checkout.py: preserve/hash all28 under an exclusive WORK
backup, move only the26 verified untracked collisions, restore only the two
backed-up tracked paths to current HEAD, git pull --ff-only, then recheck all
file hashes and unchanged S2 core code. Pending user approval; the script has
not run. Do not push this preparation before recovery because its target
origin/main is explicitly pinned to abff0ced for the reviewed comparison.
Local protected-file retry audit remains clean for all30,067 files.

## Recovery completed and verified, before any job

The user approved the one-time recovery exception. Preserved all28 files under
WORK/zephyr-rtc-clock-robustness/tacc_work/20261026-git-checkout-recovery-v1;
26 untracked collisions moved, only two tracked paths restored, then git pull.
Returned backup metadata via rsync. All28 files match their retained hashes;
HEAD on both LS6 and Mac equals abff0ced99983e9b3f60dc35ee5209c8a065f831.
The subsequent git status --porcelain output is empty. The original S2 worker,
task wrapper and controller SHA-256 values match before/after. The local full
protected-file audit passes30067/30067, SHA-256
7a8bfb74eca3008823a06bf6ffc9824ac518d078ac8241d579ab1b1445446ede.
No frozen sources, ELFs, forecasts or original run directories were touched.
The backup remains on WORK. No recovery-related experiment or job was run.

E3532543 remained PENDING Priority with zero elapsed and no start. The user
explicitly approved resubmission at12h if pending. Scheduling amendment entered
DESIGN before actions. Planned E replacement: normal /TRA25006, one node,
12:00:00, expected8SU, reservation ceiling12SU, original gates and manifests
unchanged. Recheck state/unused output before pending-only cancellation and
avoid a duplicate if the original starts. E2 and paper remain held.
