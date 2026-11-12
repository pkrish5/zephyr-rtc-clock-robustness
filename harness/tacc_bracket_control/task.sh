#!/bin/bash
set -euo pipefail
mode=${1:?build or run}
selected=${2:?unit or task index}
test "${SLURM_JOB_PARTITION:?}" = development
case "${SLURM_JOB_ACCOUNT:?}" in CCR26073|ccr26073) ;; *) exit 2;; esac
case "$mode" in
 build) args=(--unit "$selected"); limit=2100;;
 run) args=(--index "$selected"); limit=900;;
 *) exit 2;;
esac
bundle=$RTC_REFERENCE_BUNDLE
output=$RTC_JOB_OUTPUT/control
rel=$RTC_REFERENCE_OUT_REL
mkdir -p "$output" "$RTC_JOB_OUTPUT/processes/$mode" "$RTC_JOB_OUTPUT/resources/$mode" "$RTC_JOB_OUTPUT/stdout/$mode"
private=$(mktemp -d "$RTC_NODE_BASE/$mode-$selected.XXXXXX")
mkdir -p "$private/home/.config/renode" "$private/tmp" "$private/work"
cp -a "$bundle/renode-cache/." "$private/home/.config/renode/"
set -o noclobber
exec > "$RTC_JOB_OUTPUT/stdout/$mode/$selected.log" 2>&1
set +e
/usr/bin/time -v -o "$RTC_JOB_OUTPUT/resources/$mode/$selected.time" \
 timeout --signal=TERM --kill-after=30s "$limit" \
 apptainer exec --cleanenv --containall --home "$private/home:/home/rtc" --pwd /bundle \
 --bind "$bundle:/bundle:ro" --bind "$output:/bundle/$rel:rw" \
 --bind "$bundle/renode:/renode:ro" --bind "$RTC_REPO:/repo:ro" \
 --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
 --bind "$RTC_REPO/harness/tacc_s2_references:/reference-adapter:ro" \
 --bind "$RTC_REPO/subjects/counter_bracket_20261112_v1:/reference-app:ro" \
 --bind "$RTC_BUILD_BASE:/scratch-builds:rw" \
 --bind "$private/tmp:/tmp:rw" --bind "$private/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
 --env "RTC_REFERENCE_PLAN_SHA256=$RTC_REFERENCE_PLAN_SHA256" \
 --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" --env "RTC_NODE_NAME=$(hostname -f)" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
 --env "SLURM_JOB_ACCOUNT=$SLURM_JOB_ACCOUNT" \
 "$RTC_IMAGE" /opt/rtc-python/bin/python /reference-adapter/driver.py "$mode" "${args[@]}"
status=$?
set -e
python3 - "$RTC_JOB_OUTPUT/processes/$mode/$selected.json" "$status" "$selected" "$mode" <<'PY'
import json,os,sys
with open(sys.argv[1],'x') as f:
 json.dump(dict(exit_code=int(sys.argv[2]),selected=sys.argv[3],mode=sys.argv[4],
  slurm_job_id=os.environ['SLURM_JOB_ID'],account=os.environ['SLURM_JOB_ACCOUNT']),f,indent=2)
 f.write('\n')
PY
exit "$status"
