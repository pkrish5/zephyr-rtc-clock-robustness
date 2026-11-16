#!/bin/bash
set -euo pipefail
mode=${1:?}
case "$mode" in off|on) ;; *) exit 2;; esac
out=$RTC_JOB_OUTPUT/$mode
mkdir -p "$RTC_JOB_OUTPUT/processes" "$RTC_JOB_OUTPUT/stdout"
private=$(mktemp -d "$RTC_NODE_BASE/observer-$mode.XXXXXX")
mkdir -p "$private/home/.config/renode" "$private/tmp" "$private/work"
cp -a "$RTC_COUNTER_BUNDLE/renode-cache/." "$private/home/.config/renode/"
set -o noclobber
exec > "$RTC_JOB_OUTPUT/stdout/$mode.log" 2>&1
set +e
timeout --signal=TERM --kill-after=30s 2760 apptainer exec --cleanenv --containall \
 --home "$private/home:/home/rtc" --pwd /bundle \
 --bind "$RTC_COUNTER_BUNDLE:/bundle:ro" --bind "$out:/bundle/$RTC_BOUNDARY_OUT_REL:rw" \
 --bind "$RTC_COUNTER_BUNDLE/renode:/renode:ro" --bind "$RTC_REPO:/repo:ro" \
 --bind "$private/tmp:/tmp:rw" --bind "$private/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
 --env "RTC_BOUNDARY_EXECUTION_SHA=$RTC_BOUNDARY_EXECUTION_SHA" \
 --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" --env "RTC_NODE_NAME=$(hostname -f)" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
 --env "SLURM_JOB_ACCOUNT=$SLURM_JOB_ACCOUNT" "$RTC_IMAGE" /opt/rtc-python/bin/python \
 /repo/notes/counter_boundary_recovery_2026-11-16_v1/worker.py "$mode"
status=$?
set -e
python3 - "$RTC_JOB_OUTPUT/processes/$mode.json" "$status" <<'PY'
import json,sys
with open(sys.argv[1],'x') as f:json.dump({'exit_code':int(sys.argv[2])},f)
PY
exit "$status"
