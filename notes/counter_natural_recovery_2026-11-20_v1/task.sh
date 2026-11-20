#!/bin/bash
set -euo pipefail
mode=${1:?};index=${2:?}
case "$mode" in
 build) limit=540;;
 run) limit=$(python3 - "$RTC_NATURAL_BUNDLE/plan.json" "$index" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));print(3660 if p['tasks'][int(sys.argv[2])]['stage']=='nominal' else 21060)
PY
);;
 *) exit 2;;
esac
private=$(mktemp -d "$RTC_NODE_BASE/natural-$mode-$index.XXXXXX")
mkdir -p "$private/home/.config/renode" "$private/tmp" "$private/work" "$RTC_JOB_OUTPUT/processes/$mode" "$RTC_JOB_OUTPUT/stdout/$mode"
cp -a "$RTC_NATURAL_BUNDLE/renode-cache/." "$private/home/.config/renode/"
set -o noclobber
exec > "$RTC_JOB_OUTPUT/stdout/$mode/$index.log" 2>&1
set +e
timeout --signal=TERM --kill-after=30s "$limit" apptainer exec --cleanenv --containall --home "$private/home:/home/rtc" --pwd /bundle \
 --bind "$RTC_NATURAL_BUNDLE:/bundle:ro" --bind "$RTC_JOB_OUTPUT:/bundle/$RTC_NATURAL_OUT_REL:rw" \
 --bind "$RTC_NATURAL_BUNDLE/renode:/renode:ro" --bind "$RTC_REPO:/repo:ro" --bind "$RTC_BUILD_BASE:/scratch-builds:rw" \
 --bind "$private/tmp:/tmp:rw" --bind "$private/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" --env "RTC_NATURAL_EXECUTION_SHA=$RTC_NATURAL_EXECUTION_SHA" \
 --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" --env "RTC_NODE_NAME=$(hostname -f)" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" --env "SLURM_JOB_ACCOUNT=$SLURM_JOB_ACCOUNT" \
 "$RTC_IMAGE" /opt/rtc-python/bin/python /repo/notes/counter_natural_recovery_2026-11-20_v1/worker.py "$mode" "$index"
status=$?
set -e
python3 - "$RTC_JOB_OUTPUT/processes/$mode/$index.json" "$status" <<'PY'
import json,sys
with open(sys.argv[1],'x') as f:json.dump({'exit_code':int(sys.argv[2])},f)
PY
exit "$status"
