#!/bin/bash
set -euo pipefail
index=${1:?original task index}
test "${SLURM_JOB_PARTITION:?}" = normal
: "${RTC_COUNTER_BUNDLE:?}" "${RTC_JOB_OUTPUT:?}" "${RTC_NODE_BASE:?}" "${RTC_COUNTER_STAGE:?}"
out="$RTC_JOB_OUTPUT"
mkdir -p "$out/resources" "$out/stdout" "$out/processes"
private=$(mktemp -d "$RTC_NODE_BASE/task-$index.XXXXXX")
mkdir -p "$private/home/.config/renode" "$private/tmp" "$private/work"
cp -a "$RTC_COUNTER_BUNDLE/renode-cache/." "$private/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/$index.log" 2>&1
set +e
/usr/bin/time -v -o "$out/resources/$index.time" timeout --signal=TERM --kill-after=30s 1800 \
 apptainer exec --cleanenv --containall --home "$private/home:/home/rtc" --pwd /bundle \
 --bind "$RTC_COUNTER_BUNDLE:/bundle:ro" --bind "$out:/bundle/$RTC_COUNTER_OUT_REL:rw" \
 --bind "$RTC_COUNTER_BUNDLE/renode:/renode:ro" --bind "$RTC_REPO:/repo:ro" \
 --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
 --bind "$RTC_REPO/harness/tacc_counter_repair:/counter:ro" \
 --bind "$private/tmp:/tmp:rw" --bind "$private/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
 --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" --env "RTC_NODE_NAME=$(hostname -f)" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
 "$RTC_IMAGE" /opt/rtc-python/bin/python /counter/worker.py --bundle /bundle \
 --stage "$RTC_COUNTER_STAGE" --index "$index"
status=$?
set -e
python3 - "$out/processes/$index.json" "$status" "$index" <<'PY'
import json,os,sys
with open(sys.argv[1],'x') as f:
 json.dump(dict(exit_code=int(sys.argv[2]),index=int(sys.argv[3]),slurm_job_id=os.environ['SLURM_JOB_ID']),f,indent=2)
 f.write('\n')
PY
exit "$status"
