#!/bin/bash -l
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
stage=${1:?build/run}
index=${2:?index}
case "$stage" in build|run);; *) exit 2;; esac
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/$out_rel"
mkdir -p "$out/resources/$stage" "$out/stdout/$stage" "$RTC_BASE/runtime"
runtime_dir=$(mktemp -d "$RTC_BASE/runtime/${SLURM_JOB_ID}-${stage}-${index}.XXXXXX")
mkdir -p "$runtime_dir/home/.config/renode" "$runtime_dir/tmp" "$runtime_dir/work"
cp -a "$RTC_BUNDLE/renode-cache/." "$runtime_dir/home/.config/renode/"
export APPTAINERENV_XDG_CACHE_HOME=/var/tmp
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
set -o noclobber
exec > "$out/stdout/$stage/$index.log" 2>&1
test ! -e "$out/resources/$stage/$index.time"
limit=$(python3 - "$RTC_BUNDLE/plan.json" "$stage" "$index" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));stage=sys.argv[2];i=int(sys.argv[3])
if stage=='build':print(p['build_timeout_seconds']+120)
else:
    unit=next(u for u in p['units'] if u['id']==p['tasks'][i]['unit_id'])
    print(unit['wall_timeout_seconds'])
PY
)
set +e
/usr/bin/time -v -o "$out/resources/$stage/$index.time" timeout --signal=TERM --kill-after=30s "$limit" \
    apptainer exec --cleanenv --containall \
    --home "$runtime_dir/home:/home/rtc" --pwd /bundle \
    --bind "$RTC_BUNDLE:/bundle:ro" --bind "$out:/bundle/$out_rel:rw" \
    --bind "$RTC_BUNDLE/renode:/renode:ro" \
    --bind "$RTC_REPO/harness/tacc_s2:/s2:ro" \
    --bind "$runtime_dir/tmp:/tmp:rw" --bind "$runtime_dir/work:/var/tmp:rw" \
    --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
    --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
    --env "RTC_NODE_NAME=$(hostname -f)" --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
    --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
    "$RTC_IMAGE" /opt/rtc-python/bin/python /s2/worker.py --bundle /bundle --stage "$stage" --index "$index"
status=$?
set -e
# Preserve abnormal process exits as infrastructure missingness, never as test fails.
python3 - "$out/processes/$stage/$index.json" "$status" "$stage" "$index" <<'PY'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True)
with p.open('x') as f:json.dump(dict(exit_code=int(sys.argv[2]),stage=sys.argv[3],index=int(sys.argv[4]),
    slurm_job_id=os.environ['SLURM_JOB_ID']),f,indent=2)
PY
exit "$status"
