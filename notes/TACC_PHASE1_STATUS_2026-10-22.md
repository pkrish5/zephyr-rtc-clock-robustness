# Lonestar6 Phase 1 preparation, 2026-10-22

The implementation and prospective calibration amendment are in
`harness/tacc_phase1/` and `paper/DESIGN.md`. The manuscript and its existing
uncommitted edits were not changed during this preparation. No firmware
generation, Renode simulation, container build or Slurm submission has run.

Original binaries exist locally and were checked against the saved hashes,
including all 16 forecast-only binaries. The planned calibration selects
the three flipping pending suites and five complete-passing suites across
model/prompt/task strata, with 102 settings per suite. The resource probe
has its own namespace. Runtime and calibration records cannot be retried
or replaced in place.

The user authorized reuse of `ssh ls6`, restricted all remote work to
`$WORK/zephyr-rtc-clock-robustness`, and authorized development jobs under
`TRA25006`. Pin `tacc-apptainer/1.4.1` and `launcher/3.10`; require separate
approval before any normal-queue job.

The first noninteractive read-only SSH preflight stalled after printing:

```text
/work is mounted not "FULL" nor "IDLE"!
```

It returned neither the requested WORK path nor repository status. Only
the agent's own stalled SSH client was terminated. No SSH/account setting
was edited, no authentication was attempted, and no reconnection was
attempted after reporting the problem. Await the user's confirmation that
the existing session can execute a command normally before remote work.

Official release metadata verified during preparation: Renode Linux
portable archive SHA-256
`4ba7c68b59e2447f188ef4b4b112fcccd2802582c460beedceb63b84e5605a5f`;
SDK 0.17.4 Linux x86_64 minimal archive SHA-256
`a7258bf50c892c4669712b2aacdfcd5e303245bcf36cb458a296039a664594f5`.
The Renode Linux archive embeds .NET 8.0.12, while the original environment
reported .NET 8.0.21. The image definition therefore selects the external
8.0.21 runtime, with a strict version check before the resource probe.
This Linux image has not yet been built or validated; no image hash or
calibration agreement is claimed.

## User-authorized SSH retry, 2026-10-22

After the user requested another attempt, a noninteractive read-only check
returned `WORK=/work/10970/pk23377/ls6` and `/usr/bin/sbatch` with exit 0.
The conditional repository HEAD check printed no HEAD, so the expected
checkout has not been confirmed. A subsequent read-only directory check
timed out after 35 seconds without output; its SSH client was terminated
by the timeout. Authentication prompts were disabled. Remote work stopped
again under the user's connection-failure rule. No remote files were
modified, no bundle was transferred, and no jobs were submitted.

## Connection restored and first development build, 2026-10-22

On the next user-authorized retry, SSH succeeded. The authorized project
directory was absent; it was initialized there and populated using
`git pull` from the public repository at d4fd0a8319f714a96d9c94f2f13526e579ae05ae.
The sealed v1 input bundle transferred successfully. Development job
3529750, allocation TRA25006, stopped during pinned module loading with
`BASH_COMPLETION_DEBUG: unbound variable`; no image or Renode run occurred.

The module wrapper now suspends nounset only during module loading.
Ten infrastructure unit tests and shell syntax checks pass. A separate
v2 bundle preserves the same 816 calibration tasks and expected local
verdicts (776 pass, 40 fail), with plan SHA-256
`35f10f450591f8c3f393e813c2e6a3a77d79dde1343b98fdc48780c7fb434fb8`.
The next attempt uses `tacc_work/20261022-v2`; v1 and its job logs remain.

The corrected code was published locally as commit
`12393ae21169ba3915100850362137684968f3a8` and pulled on LS6.
The v2 input bundle transferred successfully. The second container-build
attempt was submitted as development job 3529760 under TRA25006
(one whole node, two-hour wall limit). Its outcome is not yet known.

Job 3529760 stopped on compute node c308-005 before the image build,
because the strict version check rejected the exact TACC package string
`apptainer version 1.4.1-1.el8`. v3 explicitly accepts that string with the
pinned module and records it unchanged. Its sealed plan SHA-256 is
`c9c0fdc77590ec6eb7b27e5244599e9ce3c9a26435b7019d8a621b5f5f818915`.
No Renode run or successful image exists yet.

The v3 compatibility fix was published from the Mac as commit 93877b24.
The next noninteractive SSH command (git pull plus v3 directory preparation)
timed out after 35 seconds with no output. Its completion is unconfirmed.
Remote work stopped under the connection-failure rule. No v3 bundle
transfer or build submission was attempted. The v2 failed-job logs have
not yet been retrieved locally; they remain under the authorized WORK
project directory. Only v1 failed-job logs were copied back. No image hash,
resource measurement, or calibration agreement is available.

## Connection restored again and v3 build queued, 2026-10-22

After the user's confirmation, SSH succeeded and the checkout pulled commit
93877b24. The sealed v3 bundle transferred successfully. Development build
3529805 was submitted under TRA25006 (one node, two-hour limit). Slurm
estimated 2026-10-22 21:26:58 Central as its start; that estimate can change.
The development partition reported 15 allocated and three drained nodes.
The v2 failed-job logs were retrieved to the local v2 artifact.
No resource measurement or Renode run has occurred at this checkpoint.

Development resource probe 3529827 was queued with
`afterok:3529805` and `--kill-on-invalid-dep=yes`, so it cannot launch unless
the build job completes successfully, including strict image sealing.
It requests one node and 20 minutes under TRA25006. Calibration remains
unsubmitted until the probe agrees and its resource measurements are read.

Job 3529805 ran on c302-006 for 39 seconds and failed during apt setup
(setgroups/seteuid errors in a root-mapped namespace without a fakeroot
helper). Probe 3529827 was cancelled without running. No image or Renode
result exists. v4 adds a checksum-pinned WORK-only fakeroot helper compiled
on the development node and a build-home mount marker guard. Its plan SHA
is `770d53b021db67a69ec2becf71b95a3067721a425cd855d328f0cead258539fa`.
The same 816 saved calibration tasks remain selected.

The v4 code was published locally as 342f9811 and pulled on LS6.
Development build 3529840 (one node, two hours) and dependent resource
probe 3529851 (one node, 20 minutes, afterok:3529840) are queued under
TRA25006. The probe cannot launch if image sealing fails. v3's image-build
log and Slurm logs are now retained in the local v3 artifact.

Job 3529840 failed after 23 seconds in helper compilation: configure found
capset but no sys/capability.h, leaving missing capability typedefs. Probe
3529851 was cancelled without running. Compiler/configure logs were copied
to the local v4 artifact. v5 disables only this optional fakeroot wrapper
using ac_cv_func_capset=no and records that choice in helper provenance.
The new plan SHA-256 is
`338081f7331ed673b493832fee6b979bccc1a3e12b1515a4140c93656df35e24`;
the same 816 tasks remain locked. No image or Renode result exists yet.
