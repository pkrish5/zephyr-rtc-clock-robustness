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

The v5 fix was published locally as 3ec18466 and pulled on LS6. The v5
bundle transferred successfully, and development build 3529884 was
submitted under TRA25006 (one node, two hours). No v5 probe is submitted
at this checkpoint.

The v5 helper compiled and installed on c302-006, and Apptainer found it.
The build passed the WORK-home guard and progressed through apt package
installation, beyond the v3 failure. Resource probe 3529889 was queued
with afterok:3529884 and kill-on-invalid-dep. No Renode run has occurred
at this checkpoint; image sealing is still pending.

Build 3529884 and dependent probe 3529889 were cancelled after inspection
showed Apptainer build configuration retains automatic host /tmp mounts.
The build ran 4:23; the probe never ran. Its log shows temporary pip paths
and the Renode archive under /tmp, so the tools may have created/cleaned
temporary build files outside WORK. This storage-boundary deviation is
recorded in DESIGN.md. No cleanup outside the project is attempted.
v6 explicitly binds WORK tmp/var-tmp for image build and inventory, with
marker guards before package operations and in image tests. Plan SHA-256:
`3db87243286fee74597053391c5c985ef19dcb45492ed5bfeb15b9e822d19acd`.
There is still no sealed image or Renode simulation result.

The v6 storage fix was published locally as fc9db144 and pulled on LS6.
The sealed v6 bundle transferred successfully. Development image build
3529906 was submitted under TRA25006 (one node, two-hour limit). No v6
probe is submitted at this checkpoint.

The v6 build passed the home, /tmp and /var/tmp WORK-marker guards and
entered apt package installation on c302-006. Resource probe 3529910 is
queued with afterok:3529906 and kill-on-invalid-dep. Full calibration is
still unsubmitted pending probe agreement and resource measurements.

Build 3529906 reached SDK setup after passing storage guards and verifying
Renode/Zephyr/module/SDK source pins. SDK setup could not find CMake on its
build-time PATH; the pinned wheel was installed in the venv, whose PATH
was previously set only for runtime. The same checksum-verified SDK archive
was copied back and its setup.sh inspected: it also requires wget and which.
v7 adds the venv build PATH, explicit wget/debianutils and early command
checks. New plan SHA-256:
`b96bd1752570e9e79ea4b78ccf1febd55eb8b116b001671e594a191beb896682`.
No sealed image or Renode simulation result exists at this checkpoint.

Build 3529906 failed after 6:31; dependent probe 3529910 was cancelled
without running. The v7 code was published locally as ef258db5 and pulled
on LS6; the sealed v7 bundle transferred successfully. Development build
3529922 was submitted under TRA25006 (one node, two-hour limit). No v7
probe is submitted at this checkpoint.

Preflight archive inspection identified omitted runtime configProperties
in the custom launcher. Pending job 3529922 was cancelled with zero elapsed
time before execution. v8 derives the config directly from the original
archive, preserving all four original properties while selecting external
.NET 8.0.21 with roll-forward disabled. A local config transformation check
confirms property preservation. v8 plan SHA-256:
`01c1f6db06ae0dd6b4f8002561fa4271644edd62083e5064fc7cc234f26aa740`.
No image or Renode simulation exists yet.

## Transfer timeout and stop, 2026-10-22

v8 was published locally as 7a4edf286ad2da25dcad0755ed5fe53f8428c12e
and the LS6 checkout successfully pulled it. The v8 transfer then reported
`rsync(77536): error: poll: timeout` under a 45-second inactivity timeout.
Remote work stopped under the connection-failure rule. Only the agent's
own rsync client was terminated; no user SSH master/account settings were
changed. The v8 bundle transfer is unconfirmed and may be partial. No v8
build/probe/calibration was submitted. All previously submitted jobs are
failed or cancelled; 3529922 was cancelled while pending. There is no
sealed SIF hash, resource measurement or calibration agreement. Resume only
after the user confirms connection availability, using the same sealed v8
bundle and verifying hashes before submission.

## Authorized retry, 2026-10-22

After the user requested another retry, the read-only SSH check succeeded.
The sealed v8 rsync completed (1,830 files; no remaining changed files),
and the remote plan SHA-256 matched
`01c1f6db06ae0dd6b4f8002561fa4271644edd62083e5064fc7cc234f26aa740`.
The LS6 checkout is at `7a4edf286ad2da25dcad0755ed5fe53f8428c12e`.
Development build **3529954** was submitted under TRA25006, one node,
two-hour wall limit. No probe or calibration has been submitted yet.

Development probe **3529956** is queued with `afterok:3529954` and
`kill-on-invalid-dep=yes`. It cannot execute after a failed image build.
Full calibration remains unsubmitted pending probe agreement and capacity.

Build 3529954 created the SIF but failed during software inventory after
7:28 because Git rejected the container checkout's ownership. Probe
3529956 was cancelled with zero runtime. No simulation occurred.
A read-only image inspection was submitted as development job 3530002
(one node, five minutes, TRA25006), recording SIF hash and actual pinned
launcher version and using only a command-scoped safe.directory option.
It does not change Git/account settings or run firmware. The original
build log and failed inventory remain retained.

Inspection job **3530002** completed successfully in five seconds on
`c304-006.ls6.tacc.utexas.edu`. Apptainer reports
`apptainer version 1.4.1-1.el8`. The created, unsealed SIF SHA-256 is
`1f10025ee9d9b5e291c9d518ac65646c79e2f833886f96561c5259cb4c86d2b4`.
Its pinned launcher reports `1.17.0+20260907gitf1dd1b4af` and `.NET 8.0.12`,
whereas the frozen plan expects `1.17.0+20260906gitf1dd1b4af` and `.NET 8.0.21`.
`dotnet --list-runtimes` lists external 8.0.21. This does not establish which
part of Renode's reported runtime is build metadata; no equivalence is
assumed. Compiler 12.2.0 and Zephyr commit match the pins.

Stopped before probe/calibration because full Renode version identity has
not been established. Do not relax the plan/version/trace gate or rerun
scientific cases without resolving this checkpoint. No active Phase 1
jobs remain, no normal submission occurred, and no firmware test ran.
The build and inspection logs were copied back with rsync to
`artifacts/tacc_phase1_20261022_v8/returned-slurm/` and the build log to
`returned-images/`. The SIF remains in WORK; no image.json seal exists.

## Approved resolution and v9, 2026-10-22

The user authorized checking official platform-package provenance, pinning
the actual runtime where feasible, and proceeding to probe/calibration with
exact raw trace and verdict agreement as the deciding test.
Development diagnostic 3530040 traced bundled 8.0.12 selection. Diagnostic
3530042 failed to find Infrastructure.dll when the derived deps file was
placed away from the application; no firmware ran. Diagnostic **3530044**
passed when the deps file was colocated with the application: --version
reports .NET 8.0.21 and the host trace confirms CoreCLR is loaded from
`/usr/share/dotnet/shared/Microsoft.NETCore.App/8.0.21/libcoreclr.so`.
Only the bundled runtimepack is removed from the derived deps manifest.

The official macOS asset checksum and mounted-original executable, assembly,
manifests and platform hashes match. Both release packages embed source
revision f1dd1b4af7838b45a925c17603cdfed0a583844a; the current v1.17.0 ref
points to a different commit. Full evidence is in
`notes/TACC_PHASE1_RENODE_PROVENANCE_2026-10-22.json`.

Published local code **11741f28** was pulled on LS6. Sealed v9 bundle
`e7fed249d4931344bbb022d4d63efec5435093cc1d7c92934de15f09ea00e0c9`
transferred successfully. Its 816 tasks, inputs and comparison criteria
match v8 exactly. Development build **3530049** derives from the hash-verified
v8 SIF with a 20-minute limit. Probe **3530050** has afterok:3530049 and a
10-minute limit. Both are one-node TRA25006 jobs. No full calibration or
production has been submitted.

## Status-command timeout and stop, 2026-10-22 (local date)

The read-only status command timed out at 45 seconds after returning
squeue / squeue --start output. Its partial stdout showed build 3530049
PENDING (Resources) and probe 3530050 PENDING (Dependency), with estimated
build start 2026-10-22T23:50:28 Central. No sacct/log output returned.
This may be a stalled accounting command rather than loss of SSH; the
cause is unconfirmed. No new remote commands were attempted after timeout,
and no credentials or account settings were requested/changed.

Existing jobs were not cancelled or resubmitted and may execute while
monitoring is stopped. The afterok probe is guarded by image/input checks
and exact verdict/trace equality; full calibration is NOT queued, and no
production is submitted. Ask the user to confirm usable access, then first
inspect these same job IDs and retained outputs. Never repeat completed
calls or overwrite records. No rebuilt-image hash or probe/calibration
outcome has been observed yet. Runtime pinning itself was verified in
diagnostic 3530044; it is not a calibration result.

## 2026-10-23 restored access: sealed image, probe infrastructure stop

The user restored access and authorized continuation. Inspection of the
existing jobs found build 3530049 had completed image sealing. New SIF
SHA-256: `831dffc44d479a06ed7945a68bd746302319d2160edb19d731e3f0cd380d4239`.
The seal records Renode Linux build 20260907 / f1dd1b4af with actual .NET
8.0.21 and Apptainer `1.4.1-1.el8`. The original local build version is
retained separately. The image sealed at 2026-10-23 04:57 UTC (October 22,
23:57 Central).

Probe 3530050 passed host input/image preflight but failed to launch the
calibration adapter: `/opt/rtc-python/bin/python: can't open file
'/opt/rtc-code/harness/tacc_phase1/calibration.py': [Errno 13] Permission
denied`. STOP.json records process exit 2. No firmware ran, no Renode
resource measurement or selected-case verdict exists, and no trace-hash
comparison was possible. All eight suite calibrations are unrun (0/816).
No further jobs were submitted. Image/build/probe/STOP logs were returned
with rsync. `phase1_checkpoint_report.json` in the local v9 artifact lists
all eight missing suite comparisons explicitly.

A scoped permission correction is prepared locally, not deployed: grant
ordinary-user read/traverse access only to `/opt/rtc-code` inside the new
image, and make image inventory execute adapter --help as the ordinary
container user before sealing. This is not a firmware execution. Do not
overwrite the v9 SIF or failed attempt; any authorized retry must use a
new sealed bundle/output directory and preserve the exact calibration
inputs and verdict/hash comparison. No calibration-validated environment
equivalence is claimed. Await user approval before further jobs.

## 2026-10-23 standing approval: permission attempt v10

Cause: v9 probe 3530050 could not read the container adapter; firmware never
started. Fix: grant read/traverse access to the image harness tree and run
adapter --help as the ordinary runtime user before sealing. No adapter,
simulation, resource, Launcher, input, forecast, or comparison logic changes.
The user grants standing approval for infrastructure-only development
resubmissions, with a three-consecutive-failure stop. Conservatively track
v9 as failure 1; v10 is the next attempt. No normal job is authorized.

Before/after audit: **29,634 protected files unchanged**, including all
tracked harness/generated/results/analysis/subjects files and additional
manifest-referenced frozen files; all **1,755** prior sealed input hashes
match both bundles and originals. Scientific task list and plan fields
are unchanged. Full per-file before/after SHA-256 log:
`artifacts/tacc_phase1_20261023_v10/hash_audit.json`, SHA-256
`6d52e9179d54993ec4f49671825988b6f004c437a7974f1b52ff61f70e774ea5`.
Sealed v10 plan SHA-256:
`aed1c266d9bbc2c962f57d882c4337ac3a7b1d3e2590c1ff29e453cb8e6d5e66`.

Only permitted packaging files differ:

| File | Before SHA-256 (v9) | After SHA-256 (v10) |
|---|---|---|
| `harness/tacc_phase1/build_image.sh` | `16e32c742214b750eb6fc65d56459bbe709a81cdbd49466f59d963abf10ed650` | `74824ac15b59624b42ae0fb8fa2d598820c41f49eee1f144315bd7daae9a4f45` |
| `harness/tacc_phase1/rtc-ls6-runtime.def` | `d85332e08fbffea23fd50f8e9bd13ea09e47d2e6652720f225e02575c92cb64a` | `cce95dfc23a3e2734861d0cbcd6a67a2891e248e9b454fa23ae440a427aed2f8` |
| `harness/tacc_phase1/rtc-ls6.def` | `0dd545e55e86596e30e8970f4b46c8cc9502c82a196b79a7c55aa056fabcf3df` | `0f044280dc1c4a8a4ac5b071cdf0e455d4d432ba2ed13838b0a61bcde3afe9e4` |

Code 2a82f905 was published locally and pulled on LS6. The v10 bundle and
hash audit transferred and matched their seals. Development build
**3531417** is submitted (one node, 20-minute limit, TRA25006); probe
**3531420** is conditional on afterok:3531417 (one node, 10-minute limit).
No full calibration or normal job is submitted at this checkpoint.

Build 3531417 completed image sealing on c303-006 after the permission
fix and ordinary-user adapter --help check passed. New image SHA-256:
`94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
Renode reports .NET 8.0.21; the exact approved Linux build string matches.
The seal and software inventory are copied back under returned-images.
Probe agreement is still pending; no calibration submission yet.

Probe **3531420** passed exactly on c303-006. The expected and observed
complete raw trace SHA-256 is
`36fa96cf49940ff1f5f850dc641d3a131374d0c0b3f8956a0d11248d4461dabc`,
with the same pass verdict (Astra base callback r01, 17 kHz). Local audit
recomputed both original and new trace hashes from returned raw files and
verified the recorded SIF hash. Peak RSS 320,488 KiB (313 MiB), wall 83.4 s,
128 CPUs and 255,925,244 KiB available node memory were measured.
The successful probe resets the consecutive infrastructure-failure count
to zero. This is one resource-probe agreement, not 816-case calibration.

The locked rule chooses cap 32 (memory limit alone permits 425). The
conservative aggregate allowance is 14.67 GiB versus 195.26 GiB (80% of
measured available memory). For 816 cases the estimate is 3,372.6 s
(56.21 min), 0.9368 node-hour/SU at the documented one-SU/node-hour rate,
with a 90-minute requested upper reservation of 1.5 SU. This is an estimate
from one probe, not measured packed throughput. Proceed with one packed
development node under TRA25006; no normal-queue approval is implied.

Packed calibration **3531436** was submitted to development under TRA25006:
one whole node, 128 allocated CPUs, cap 32, 90-minute wall limit. All
816 jobfile commands invoke one apptainer exec each; no Slurm array is
used. No normal job is submitted. Stop after its report or any mismatch.

## 2026-10-23 Phase 1 calibration complete: STOP for user approval

Development calibration **3531436** completed successfully on
`c303-006.ls6.tacc.utexas.edu`, exit 0:0, in **1,009 seconds (16:49)**
(17:03:11--17:20:00 Central, according to Slurm accounting).
All **816/816 verdicts and 816/816 complete raw trace-file SHA-256 values
match** the frozen originals. All eight suites have 102/102 matches for
both measures (100 saved seeds plus two endpoints). There are **776 passes,
40 expected assertion failures, zero missing cases and zero mismatches**.
The separate resource probe also matched; it is not added to the 816-case
calibration denominator.

| Frozen suite | Cases completed | Verdict matches | Raw trace SHA-256 matches |
|---|---:|---:|---:|
| `astra-range_absent-rtc_alarm_callback-r01` | 102/102 | 102/102 | 102/102 |
| `astra-range_absent-rtc_alarm_pending-r05` | 102/102 | 102/102 | 102/102 |
| `astra-range_present-rtc_alarm_pending-r01` | 102/102 | 102/102 | 102/102 |
| `luna-range_absent-rtc_time_counting-r01` | 102/102 | 102/102 | 102/102 |
| `luna-range_present-rtc_time_counting-r01` | 102/102 | 102/102 | 102/102 |
| `sol-range_absent-rtc_alarm_pending-r01` | 102/102 | 102/102 | 102/102 |
| `sol-range_absent-rtc_alarm_pending-r03` | 102/102 | 102/102 | 102/102 |
| `sol-range_present-rtc_alarm_callback-r01` | 102/102 | 102/102 | 102/102 |

The macOS ARM64 and Linux x86_64 portable packages embed the same
`f1dd1b4af7838b45a925c17603cdfed0a583844a` source revision, but their build
dates differ (20260906 versus 20260907), as recorded in the provenance
note. The actual runtime is now .NET 8.0.21 on both. This environment
difference is **disclosed and calibration-validated for these eight suites
and 816 saved cases**; no broader platform or silicon equivalence is claimed.
The current v1.17.0 ref differs from the embedded asset revision, so the
checksum-pinned official assets and embedded revision remain the anchors.

SIF SHA-256:
`94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
Every calibration record contains node, SIF hash, Slurm ID, actual Apptainer
version `1.4.1-1.el8`, and pinned module metadata. All records show
`development`, job 3531436, and the same SIF. Launcher used 32 workers.
The maximum measured per-command peak RSS across calibration was
328,692 KiB (321 MiB), within the probe-based safety allowance; median
individual wall time was 33.08 s (range 22.2--56.21 s). These are process
measurements, not aggregate node peak memory.

All raw records, traces, monitor/UART logs, resource logs, comparisons,
Launcher logs, build/seal inventories and Slurm logs were returned by rsync
under `artifacts/tacc_phase1_20261023_v10/`. Local re-execution of the
unchanged comparison analysis recomputed raw trace and record hashes and
produced a report identical to the remote report:
`verified_calibration_report.json` (SHA-256 `2ef964ac4a41fe13733f7aa4e33019536aaf29024f9cbfac0fa4708449c551ea`).
`phase1_success_summary.json` gives the concise eight-suite summary.
`slurm_accounting.txt` records all three v10 jobs as COMPLETED.

The post-calibration audit again hashes all **29,634 protected files** and
finds no change, and confirms permitted packaging files still match the
v10 after-fix hashes. Source:
`post_calibration_hash_verification.json` (SHA-256 `e7bbefcd71c8a074c1c1f94d8ca0b288b2ece084312920ebae2eeb03de18c428`).
The prior full per-file before/after audit remains immutable. No frozen
source, ELF, forecast, original result, or harness logic was changed.

Consecutive infrastructure failures are zero after this successful attempt.
**Execution is STOPPED pending user approval. No normal-queue job or
further experiment is submitted.** Future production requires the separate
job/node/wall-time/SU proposal and approval specified by the user.


## 2026-10-24 infrastructure standing-approval handoff: Phase 2 cache path

Phase 1's completed 816/816 verdict and trace agreement remains unchanged.
Phase 2 D job 3532338 hit a shared read-only Zephyr compiler-cache path error;
the job was cancelled and its raw attempt preserved. Pending E jobs 3532458
and 3532464 were cancelled before repair execution. A new development-only
D v2 retry sets container XDG_CACHE_HOME=/var/tmp, already privately backed
by WORK, with unchanged SIF, original workers, sources, ELFs and forecasts.
The new wrapper validates task 0 once before the remaining 215 controls.
This is infrastructure attempt 2 after the initial D cache failure; stop
if three consecutive infrastructure attempts fail. Full causes, plan seals
and before/after hash audits are logged in the Phase 2 status note and DESIGN.
No normal E replacement is released until the D fix is validated.
