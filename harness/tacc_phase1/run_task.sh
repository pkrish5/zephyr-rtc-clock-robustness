#!/bin/bash -l
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
source "$script_dir/common.sh"
phase=${1:?probe or calibration}
index=${2:-0}
case "$phase" in probe|calibration) ;; *) echo 'STOP: Phase 1 only' >&2; exit 2 ;; esac
: "${SLURM_JOB_ID:?Run only within a Slurm allocation}"
test "${SLURM_JOB_PARTITION:-}" = development || { echo 'STOP: Phase 1 uses development' >&2; exit 2; }
out="$RTC_BUNDLE/study/results/tacc_phase1_20261022_v1"
test ! -e "$out/STOP.json" || { echo 'STOP: calibration stop marker exists' >&2; exit 2; }
RTC_CONTAINER_SHA256=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["container_sha256"])' "$RTC_BASE/images/image.json")
export RTC_CONTAINER_SHA256
mkdir -p "$RTC_BASE/runtime" "$out/$phase/resources" "$out/$phase/stdout"
runtime_dir=$(mktemp -d "$RTC_BASE/runtime/${SLURM_JOB_ID}-${phase}-${index}.XXXXXX")
mkdir -p "$runtime_dir/home/.config/renode" "$runtime_dir/tmp" "$runtime_dir/work"
cp -a "$RTC_BUNDLE/renode-cache/." "$runtime_dir/home/.config/renode/"
tasklog="$out/$phase/stdout/$index.log"
reslog="$out/$phase/resources/$index.time"
# Refuse to overwrite even a shell-level failure that predates a JSON record.
set -o noclobber
exec > "$tasklog" 2>&1
test ! -e "$reslog" || { echo 'STOP: original resource log exists'; exit 2; }
set +e
/usr/bin/time -v -o "$reslog" apptainer exec --cleanenv --containall \
    --home "$runtime_dir/home:/home/rtc" --pwd /study \
    --bind "$RTC_BUNDLE:/bundle:ro" \
    --bind "$RTC_BUNDLE/study:/bundle/study:ro" \
    --bind "$out:/bundle/study/results/tacc_phase1_20261022_v1:rw" \
    --bind "$RTC_BUNDLE/study:/study:ro" \
    --bind "$runtime_dir/tmp:/tmp:rw" --bind "$runtime_dir/work:/var/tmp:rw" \
    --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
    --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
    --env "RTC_LAUNCHER_MODULE=launcher/3.10" \
    --env "RTC_NODE_NAME=$(hostname -f)" \
    --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
    --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
    "$RTC_IMAGE" /opt/rtc-python/bin/python \
    /opt/rtc-code/harness/tacc_phase1/calibration.py run \
    --bundle /bundle --phase "$phase" --index "$index"
result=$?
set -e
if [ "$result" -ne 0 ]; then
    python3 - "$out/STOP.json" "$phase" "$index" "$result" <<'PY'
import json,sys
from pathlib import Path
try:
    with Path(sys.argv[1]).open('x') as f:
        json.dump({'reason':'task process failed','phase':sys.argv[2],'index':sys.argv[3],'exit_code':sys.argv[4]},f)
except FileExistsError: pass
PY
fi
# Keep WORK-backed runtime directories on failure for diagnosis; no retry.
exit "$result"
