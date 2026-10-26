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
