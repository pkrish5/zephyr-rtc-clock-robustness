#!/bin/bash
# Storage contract for new jobs. Do not source the frozen legacy common.sh.
set -euo pipefail
: "${WORK:?}" "${SCRATCH:?}" "${SLURM_JOB_ID:?compute allocation required}"
case "${SLURM_JOB_ACCOUNT:?}" in CCR26073|ccr26073) ;; *) exit 2;; esac
case "${SLURM_JOB_PARTITION:?}" in development|normal) ;; *) exit 2;; esac
: "${RTC_REPO:=$WORK/zephyr-rtc-clock-robustness}"
export RTC_REPO
# A job never creates loose build/cache/run evidence under WORK.
export RTC_JOB_BASE="$SCRATCH/zephyr-rtc-clock-robustness/jobs/$SLURM_JOB_ID"
export RTC_JOB_OUTPUT="$RTC_JOB_BASE/output"
export RTC_BUILD_BASE="$RTC_JOB_BASE/builds"
export RTC_NODE_BASE="/tmp/rtc-$USER-$SLURM_JOB_ID"
export RTC_ARCHIVE_BASE="$RTC_REPO/tacc_work/packed-results"
mkdir -p "$RTC_JOB_OUTPUT" "$RTC_BUILD_BASE" "$RTC_NODE_BASE/tmp" "$RTC_NODE_BASE/cache" "$RTC_NODE_BASE/apptainer-cache" "$RTC_NODE_BASE/apptainer-config"
export TMPDIR="$RTC_NODE_BASE/tmp"
export XDG_CACHE_HOME="$RTC_NODE_BASE/cache"
export APPTAINER_TMPDIR="$RTC_NODE_BASE/tmp"
export APPTAINER_CONFIGDIR="$RTC_NODE_BASE/apptainer-config"
export LC_ALL=C
set +u
module load tacc-apptainer/1.4.1
module load launcher/3.10
set -u
# After the module load, which sets its own shared SCRATCH cache path.
export APPTAINER_CACHEDIR="$RTC_NODE_BASE/apptainer-cache"
RTC_APPTAINER_VERSION=$(apptainer --version)
case "$RTC_APPTAINER_VERSION" in 'apptainer version 1.4.1'|'apptainer version 1.4.1-1.el8') ;; *) exit 2;; esac
export RTC_APPTAINER_VERSION RTC_LAUNCHER_MODULE=launcher/3.10
python3 - <<'PY'
import os
from pathlib import Path
work=Path(os.environ['WORK']).resolve();scratch=Path(os.environ['SCRATCH']).resolve()
repo=Path(os.environ['RTC_REPO']).resolve();repo.relative_to(work)
for name in ('RTC_JOB_BASE','RTC_JOB_OUTPUT','RTC_BUILD_BASE'):
    p=Path(os.environ[name]).resolve();p.relative_to(scratch)
    if p.is_relative_to(work):raise SystemExit('Loose output on WORK is forbidden: '+name)
for name in ('TMPDIR','XDG_CACHE_HOME','APPTAINER_TMPDIR','APPTAINER_CACHEDIR','APPTAINER_CONFIGDIR'):
    Path(os.environ[name]).resolve().relative_to(Path('/tmp').resolve())
Path(os.environ['RTC_ARCHIVE_BASE']).resolve().relative_to(repo)
PY
# Each task must use a private subdirectory of RTC_NODE_BASE for container
# home,/tmp,/var/tmp and bind RTC_JOB_OUTPUT to the locked logical output path.
# Each job must publish a verified archive before success, including on its
# documented signal/interrupt path; final records may not remain only here.
