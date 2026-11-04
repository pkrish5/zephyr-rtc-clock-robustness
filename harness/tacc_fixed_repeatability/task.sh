#!/bin/bash -l
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
test "$SLURM_JOB_PARTITION" = development
index=${1:?}
primary=${RTC_REPEAT_PRIMARY:?}
packet=${RTC_REPEAT_PACKET:?}
out=$RTC_JOB_OUTPUT
readarray -t values < <(python3 - "$primary/plan.json" "$packet/plan.json" "$index" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));n=json.load(open(sys.argv[2]));t=next(t for t in n['tasks'] if t['index']==int(sys.argv[3]));u=next(u for u in p['units'] if u['id']==t['unit_id'])
print(p['output_relative']);print(u['wall_timeout_seconds'])
PY
)
rel=${values[0]};limit=${values[1]}
runtime=$(mktemp -d "$RTC_NODE_BASE/repeat-$index.XXXXXX")
mkdir -p "$runtime/home/.config/renode" "$runtime/tmp" "$runtime/work" "$out/stdout" "$out/resources" "$out/processes"
cp -a "$primary/renode-cache/." "$runtime/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/$index.log" 2>&1
set +e
/usr/bin/time -v -o "$out/resources/$index.time" timeout --signal=TERM --kill-after=30s "$limit" \
 apptainer exec --cleanenv --containall --home "$runtime/home:/home/rtc" --pwd /bundle \
 --bind "$primary:/primary:ro" --bind "$primary:/bundle:ro" \
 --bind "$out:/bundle/$rel:rw" --bind "$primary/$rel/builds:/bundle/$rel/builds:ro" \
 --bind "$primary/renode:/renode:ro" \
 --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
 --bind "$RTC_REPO/harness/tacc_fixed_repeatability:/repeat-code:ro" \
 --bind "$packet:/repeat-packet:ro" \
 --bind "$runtime/tmp:/tmp:rw" --bind "$runtime/work:/var/tmp:rw" \
 --env XDG_CACHE_HOME=/var/tmp --env "RTC_REPEAT_UNIT=$RTC_REPEAT_UNIT" \
 --env "RTC_CONTAINER_SHA256=${RTC_CONTAINER_SHA256:?}" --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
 --env "RTC_NODE_NAME=$(hostname -f)" --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
 "${RTC_IMAGE:?}" /opt/rtc-python/bin/python /repeat-code/worker.py --index "$index"
status=$?
set -e
python3 - "$out/processes/$index.json" "$status" "$index" <<'PY'
import json,os,sys
with open(sys.argv[1],'x') as f:json.dump(dict(index=int(sys.argv[3]),exit_code=int(sys.argv[2]),slurm_job_id=os.environ['SLURM_JOB_ID']),f,indent=2);f.write('\n')
PY
exit "$status"
