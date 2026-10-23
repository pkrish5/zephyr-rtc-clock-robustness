#!/bin/bash
# Source from an LS6 login shell or Slurm job. Never changes HOME or SCRATCH.
set -euo pipefail
: "${WORK:?WORK must be set by Lonestar6}"
: "${RTC_REPO:=$WORK/zephyr-rtc-clock-robustness}"
: "${RTC_BASE:=$RTC_REPO/tacc_work/20261022}"
: "${RTC_BUNDLE:=$RTC_BASE/calibration-bundle}"
: "${RTC_IMAGE:=$RTC_BASE/images/rtc-ls6-v1.sif}"
: "${RTC_CONCURRENCY_CAP:=32}"
export RTC_REPO RTC_BASE RTC_BUNDLE RTC_IMAGE RTC_CONCURRENCY_CAP
export APPTAINER_CACHEDIR="$RTC_BASE/apptainer-cache"
export APPTAINER_TMPDIR="$RTC_BASE/apptainer-tmp"
export APPTAINER_CONFIGDIR="$RTC_BASE/apptainer-config"
export TMPDIR="$RTC_BASE/tmp"
export XDG_CACHE_HOME="$RTC_BASE/xdg-cache"
export LC_ALL=C
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" "$APPTAINER_CONFIGDIR" "$TMPDIR" "$XDG_CACHE_HOME"
# TACC's Apptainer completion script reads optional unset variables.
# Keep errexit enabled; restore nounset immediately after module loading.
set +u
module load tacc-apptainer/1.4.1
module load launcher/3.10
set -u
RTC_APPTAINER_VERSION=$(apptainer --version)
case "$RTC_APPTAINER_VERSION" in
    'apptainer version 1.4.1'|'apptainer version 1.4.1-1.el8') ;;
    *) echo "STOP: Apptainer 1.4.1 required: $RTC_APPTAINER_VERSION" >&2; exit 2 ;;
esac
case ":${LOADEDMODULES:-}:" in
    *:launcher/3.10:*) ;;
    *) echo "STOP: launcher/3.10 is not loaded" >&2; exit 2 ;;
esac
export RTC_APPTAINER_VERSION
export RTC_LAUNCHER_MODULE=launcher/3.10
python3 - "$WORK" "$RTC_REPO" "$RTC_BASE" "$RTC_BUNDLE" "$RTC_IMAGE" "$TMPDIR" <<'PY'
import sys
from pathlib import Path
work=Path(sys.argv[1]).resolve()
root=Path(sys.argv[2]).resolve()
try: root.relative_to(work)
except ValueError: raise SystemExit('The repository must remain under WORK')
for arg in sys.argv[2:]:
    try: Path(arg).resolve().relative_to(root)
    except ValueError: raise SystemExit('All project paths must remain inside the authorized repository: '+arg)
PY
