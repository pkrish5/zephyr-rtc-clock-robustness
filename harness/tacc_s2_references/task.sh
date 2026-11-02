#!/bin/bash -l
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
mode=${1:?build or run}
selected=${2:?unit or task index}
case "$mode" in build|run) ;; *) exit 2;; esac
bundle=$RTC_JOB_BASE/reference-bundle
out=$RTC_JOB_OUTPUT
rel=$(python3 - "$bundle/plan.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['output_relative'])
PY
)
runtime=$(mktemp -d "$RTC_NODE_BASE/reference-$mode-$selected.XXXXXX")
mkdir -p "$runtime/home/.config/renode" "$runtime/tmp" "$runtime/work" \
    "$out/stdout/$mode" "$out/resources/$mode" "$out/processes/$mode"
cp -a "$bundle/renode-cache/." "$runtime/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/$mode/$selected.log" 2>&1
args=(--unit "$selected")
limit=1800
if [ "$mode" = run ]; then args=(--index "$selected"); limit=900; fi
set +e
/usr/bin/time -v -o "$out/resources/$mode/$selected.time" \
 timeout --signal=TERM --kill-after=30s "$limit" \
 apptainer exec --cleanenv --containall --home "$runtime/home:/home/rtc" --pwd /bundle \
 --bind "$bundle:/bundle:ro" --bind "$out:/bundle/$rel:rw" \
 --bind "$RTC_BUILD_BASE:/scratch-builds:rw" \
 --bind "$bundle/renode:/renode:ro" \
 --bind "$RTC_REPO/subjects/s2_references_20261102_v1:/reference-app:ro" \
 --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
 --bind "$RTC_REPO/harness/tacc_s2_references:/reference-adapter:ro" \
 --bind "$runtime/tmp:/tmp:rw" --bind "$runtime/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=${RTC_CONTAINER_SHA256:?}" \
 --env "RTC_REFERENCE_PLAN_SHA256=${RTC_REFERENCE_PLAN_SHA256:?}" \
 --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
 --env "RTC_NODE_NAME=$(hostname -f)" --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
 --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
 "${RTC_IMAGE:?}" /opt/rtc-python/bin/python /reference-adapter/driver.py "$mode" "${args[@]}"
status=$?
set -e
python3 - "$out/processes/$mode/$selected.json" "$status" "$selected" "$mode" <<'PY'
import json,os,sys
with open(sys.argv[1],'x') as stream:
    json.dump(dict(exit_code=int(sys.argv[2]),subject=sys.argv[3],mode=sys.argv[4],
                   slurm_job_id=os.environ['SLURM_JOB_ID']),stream,indent=2)
    stream.write('\n')
PY
exit "$status"
