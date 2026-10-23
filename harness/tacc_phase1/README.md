# Lonestar6 Phase 1: image, resource probe and strict calibration

Current recovery attempt: v8, using `tacc_work/20261022-v8` and a sealed
`artifacts/tacc_phase1_20261022_v8` bundle. See the recovery notes below.

Status: prepared implementation. A successful local syntax/unit check does
not establish that the Linux image builds or that calibration agrees.
The agent may use the user's existing `ssh ls6` session without prompting.
If the connection fails or requests authentication, stop and report it.

All remote paths below are inside
`$WORK/zephyr-rtc-clock-robustness`. Do not edit account/SSH settings.
Pull code using `git pull` only; never push from LS6. Use the existing
clone, rather than creating a second checkout outside the approved path.
Only small file-management and submission commands run on login nodes.
Builds, Renode runs, and substantive analyses run on compute nodes.

## Frozen inputs and stopping rule

`prepare.py` reads the existing local records and makes an exclusive-create
transfer bundle with the original ELFs, sources, platforms and traces.
Nothing is rebuilt for calibration. Five passing strata and three flipping
pending suites give eight suites, each with 100 saved settings and both
endpoints (816 records). The Astra base callback at the slow endpoint is
also used once in a separate resource-probe namespace.

The original simulation loop, session adapter, observation steps and
verdict parser are reused byte-for-byte. A new wrapper redirects output
and adds execution provenance. Every record includes `node_name`,
`container_sha256`, `apptainer_version`, `slurm_job_id`, task index and
plan hash. Trace files retain the original schema and run IDs so the
**entire trace-file SHA-256** can be compared without normalization.

A missing verdict or any verdict/trace mismatch writes `STOP.json`.
No new task starts after observing this marker. Tasks already running may
finish and are retained. Exclusive task claims, no-requeue Slurm jobs and
exclusive result creation prevent retries from replacing failures.
Never clear the marker or rerun a failed task to obtain a pass.

## 1. Prepare locally, before any new experimental result

From the original Mac checkout:

```bash
cd /Users/pranavkrishnan/Development/Flakey_Tests_Embeded
python3 harness/tacc_phase1/test_infrastructure.py
python3 harness/tacc_phase1/prepare.py \
  --out artifacts/tacc_phase1_20261022_v1
python3 harness/tacc_phase1/calibration.py verify \
  --bundle artifacts/tacc_phase1_20261022_v1 --repo .
```

The plan seals code and input hashes. Any code change after preparation
requires a new bundle/version before execution. Copying the bundle does
not change frozen inputs. It includes only the SVD cache resource and
cache index; it excludes Renode history and credentials.

After the new scripts are committed/pushed locally, use the authenticated
session for the following lightweight commands. No password/token is used
by the agent:

```bash
ssh -o BatchMode=yes ls6 '
  cd "$WORK/zephyr-rtc-clock-robustness" && git pull --ff-only
  mkdir -p tacc_work/20261022/calibration-bundle tacc_work/20261022/slurm
  printf "REMOTE_WORK=%s\n" "$WORK"
'
```

Transfer only the input bundle, not a replacement code checkout. In a
local shell, obtain the path using the existing connection:

```bash
RTC_REMOTE_WORK=$(ssh -o BatchMode=yes ls6 'printf "%s" "$WORK"')
rsync -av -e 'ssh -o BatchMode=yes' \
  artifacts/tacc_phase1_20261022_v1/ \
  "ls6:$RTC_REMOTE_WORK/zephyr-rtc-clock-robustness/tacc_work/20261022/calibration-bundle/"
```

## 2. Build the image on a development compute node

In the authenticated LS6 shell:

```bash
export RTC_REPO="$WORK/zephyr-rtc-clock-robustness"
export RTC_BASE="$RTC_REPO/tacc_work/20261022"
export RTC_BUNDLE="$RTC_BASE/calibration-bundle"
export RTC_IMAGE="$RTC_BASE/images/rtc-ls6-v1.sif"
module load tacc-apptainer/1.4.1
module load launcher/3.10
mkdir -p "$RTC_BASE/slurm"
cd "$RTC_REPO"
sbatch -A TRA25006 \
  --output="$RTC_BASE/slurm/build-%j.out" \
  --error="$RTC_BASE/slurm/build-%j.err" \
  harness/tacc_phase1/build.sbatch
```

The definition digest-pins the x86_64 .NET 8.0.21 base, checks the official
Renode 1.17.0 and SDK 0.17.4 archive hashes, and checks Zephyr/module commits
against the original environment. The Linux Renode portable archive embeds
.NET 8.0.12, so a wrapper explicitly uses the pinned external .NET 8.0.21.
It refuses to seal an image whose complete Renode version differs from
the historical version. The SIF hash is written to `images/image.json`
and `images/rtc-ls6-v1.sif.sha256`; the full software inventory is saved.

Apptainer caches, temporary files, private homes, build logs and SIF are
all WORK-backed. The definition's `/opt` is inside the WORK-backed build rootfs. v6 also
explicitly binds WORK directories over `/tmp` and `/var/tmp`; setting
APPTAINER_TMPDIR alone does not isolate the build's automatic tmp mounts.
The build uses unprivileged fakeroot. If LS6 disallows that feature, or
network access from the build node fails, retain the log and report it;
do not use sudo, change account settings, or substitute an unpinned image.

## 3. Measure one run before choosing packed concurrency

After the build job succeeds:

```bash
sbatch -A TRA25006 \
  --output="$RTC_BASE/slurm/probe-%j.out" \
  --error="$RTC_BASE/slurm/probe-%j.err" \
  harness/tacc_phase1/probe.sbatch
```

This is one development node and one firmware run. GNU time reports peak
RSS and wall time; the resource report also stores node memory, CPU
availability and the calibration comparison. Read
`calibration-bundle/study/results/tacc_phase1_20261022_v1/probe/resource_report.json`.
It must say `probe_agrees`. If not, stop before calibration.

Concurrency is calculated on the calibration node as:

```text
min(requested cap, available CPUs,
    floor(0.80 * available node memory / (1.50 * measured peak RSS)))
```

The default configurable cap is 32; a single measurement is an estimate,
not a guarantee of peak memory for every suite. Each calibration run
also receives a GNU time log. The safety multiplier and initial cap limit
risk from variation between suites.

## 4. Packed calibration using Launcher 3.10

After reviewing the successful probe:

```bash
export RTC_CONCURRENCY_CAP=32
sbatch -A TRA25006 \
  --output="$RTC_BASE/slurm/calibration-%j.out" \
  --error="$RTC_BASE/slurm/calibration-%j.err" \
  harness/tacc_phase1/calibration.sbatch
```

This requests **one whole development node**, not an array. Launcher
3.10 runs one jobfile line per (suite, setting), each calling a wrapper
with exactly one `apptainer exec`. `LAUNCHER_PPN` is set to the calculated
concurrency. Local single-node mode avoids remote-host SSH retries.
Task binding is enabled. Each invocation gets its own WORK-backed home,
temporary directories, history and copied SVD cache.

The job saves `concurrency.json` with the projected wall time and SUs,
then refuses to launch if the estimate exceeds its 90-minute time limit.
Lonestar6's documented full-node charge is one SU/node-hour with a
15-minute minimum; confirm current limits/rates with `qlimits`.
The 90-minute reservation has an upper time-limit charge of 1.5 SUs for
one node at that rate. The estimate uses the measured wall time, 50%
runtime allowance and two minutes of startup, so it can be reported only
after the probe. The build and probe have separate development charges.

The report ends with `agreement_pending_user_approval` only if all 816
records agree and the probe agrees. This status **does not authorize
production**. A normal-queue job is never submitted by these scripts.
For any future production proposal, report node count, wall limit,
estimated SUs and the time-limit charge before requesting approval.

## 5. Return results, then STOP

Use rsync from the Mac with the existing authenticated connection:

```bash
rsync -av -e 'ssh -o BatchMode=yes' \
  "ls6:$RTC_REMOTE_WORK/zephyr-rtc-clock-robustness/tacc_work/20261022/images/" \
  artifacts/tacc_phase1_20261022_v1/returned-images/ \
  --exclude='*.sif'
rsync -av -e 'ssh -o BatchMode=yes' \
  "ls6:$RTC_REMOTE_WORK/zephyr-rtc-clock-robustness/tacc_work/20261022/calibration-bundle/study/results/tacc_phase1_20261022_v1/" \
  artifacts/tacc_phase1_20261022_v1/study/results/tacc_phase1_20261022_v1/
```

Include the Slurm stdout/stderr as well when diagnosing a failure. The
SIF stays on WORK; its hash, build log and inventory are returned.
Stop and send the calibration report for review. Do not execute Phase 2
or edit manuscript numbers until approval.

Sources: [LS6 guide](https://docs.tacc.utexas.edu/hpc/lonestar6/),
[Launcher](https://github.com/TACC/launcher),
[Apptainer 1.4 build options](https://apptainer.org/docs/user/1.4/cli/apptainer_build.html),
[Renode 1.17.0](https://github.com/renode/renode/releases/tag/v1.17.0),
[SDK 0.17.4](https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v0.17.4).

## LS6 module-loading correction (2026-10-22)

Development build 3529750 stopped in the Apptainer completion script under
Bash nounset, before image creation. The wrapper now disables nounset only
while loading pinned modules, then restores it. The next attempt uses
`artifacts/tacc_phase1_20261022_v2` and exports
`RTC_BASE="$RTC_REPO/tacc_work/20261022-v2"`, with bundle and image paths
derived from that base. Preserve v1 inputs and failed-job logs.

The v2 job 3529760 reached the compute node, then rejected TACC's exact
`apptainer version 1.4.1-1.el8` package string. v3 accepts that string while
retaining it in every record; the module stays pinned to 1.4.1. Use a new
`artifacts/tacc_phase1_20261022_v3` bundle and `tacc_work/20261022-v3` base.
No image or Renode run occurred in either failed build attempt.

## WORK-only fakeroot helper (v4, 2026-10-22)

Job 3529805 verified the inputs but failed at apt's setgroups/seteuid calls
because LS6 lacked a fakeroot helper. Dependent probe 3529827 was cancelled
without running. v4 builds Debian fakeroot 1.37.1.1 under the authorized
project's WORK tools directory, on the development compute node. Its source
is checksum pinned; compiler, installed-file hashes and job/node metadata
are recorded. This follows Apptainer's documented root-mapped namespace
plus host fakeroot-helper mode. No system/account settings change.

Before package commands, the image recipe checks a marker proving /root
is bound to the project's WORK-backed build home. The image manifest also
records the helper inventory hash. All simulator pins and calibration inputs
and rules stay unchanged. Latest paths to export before submitting:

```bash
export RTC_REPO="$WORK/zephyr-rtc-clock-robustness"
export RTC_BASE="$RTC_REPO/tacc_work/20261022-v4"
export RTC_BUNDLE="$RTC_BASE/calibration-bundle"
export RTC_IMAGE="$RTC_BASE/images/rtc-ls6-v1.sif"
```

Use the sealed v4 input bundle, preserve previous attempts and logs, and
submit the same build/probe/calibration scripts only to development.

The v4 helper configure test found capset but no sys/capability.h; build
3529840 therefore failed before image creation. v5 disables that optional
helper wrapper with `ac_cv_func_capset=no`, records it in the helper
inventory, and uses `artifacts/tacc_phase1_20261022_v5` and
`RTC_BASE="$RTC_REPO/tacc_work/20261022-v5"`. No system headers, account
settings or kernel capabilities are changed. Probe 3529851 was cancelled.

## Explicit build tmp mounts (v6, 2026-10-22)

The v5 helper worked and package installation proceeded. Inspection then
showed that the default build configuration can expose compute-node /tmp
and /var/tmp inside the container. The build was cancelled at 4:23 and its
dependent probe cancelled before execution. The log shows temporary pip
paths and a download under /tmp, so a WORK-only storage deviation is
possible. No cleanup outside the authorized tree is attempted.

v6 explicitly binds `RTC_BASE/build-tmp` and `RTC_BASE/build-var-tmp` over
those paths for both build and inventory, and checks WORK markers before
package commands and in the image test section. Runtime probe/calibration
wrappers already use explicit WORK-backed tmp binds. Latest transfer bundle
is `artifacts/tacc_phase1_20261022_v6`; export
`RTC_BASE="$RTC_REPO/tacc_work/20261022-v6"` and derive bundle/image paths
from that base. Preserve all earlier attempts.

## SDK build-time dependencies (v7, 2026-10-22)

v6 passed every WORK mount guard and reached SDK setup, which could not
find CMake because `%environment` does not set the `%post` PATH. v7 exports
the venv PATH during the build, explicitly installs wget/debianutils for
the SDK's wget/which checks, and checks those commands early. All runtime
pins and experiment inputs remain unchanged. Use bundle
`artifacts/tacc_phase1_20261022_v7` and
`RTC_BASE="$RTC_REPO/tacc_work/20261022-v7"`, deriving bundle/image paths.
No image or Renode simulation was produced by v6.

## Preserve original runtime properties (v8, 2026-10-22)

Before any simulation, v8 derives its .NET launcher configuration from the
archive's supplied Renode.runtimeconfig.json, preserving every original
configProperty and changing only bundled-framework selection to external
.NET 8.0.21 with rollForward disabled. This retains the original culture
handling flag. Pending build 3529922 was cancelled without executing.
Use `artifacts/tacc_phase1_20261022_v8` and
`RTC_BASE="$RTC_REPO/tacc_work/20261022-v8"`; other paths derive from it.
