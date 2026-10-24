#!/bin/bash -l
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
: "${SLURM_JOB_ID:?}"
test "${SLURM_JOB_PARTITION:-}" = normal
stage=${1:?gates/controls/evaluate}
index=${2:?index}
case "$stage" in gates|controls|evaluate);; *) exit 2;; esac
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/study/$out_rel"
test ! -e "$out/STOP.json"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
mkdir -p "$RTC_BASE/runtime" "$out/resources/$stage" "$out/stdout/$stage"
runtime_dir=$(mktemp -d "$RTC_BASE/runtime/${SLURM_JOB_ID}-${stage}-${index}.XXXXXX")
mkdir -p "$runtime_dir/home/.config/renode" "$runtime_dir/tmp" "$runtime_dir/work"
cp -a "$RTC_BUNDLE/renode-cache/." "$runtime_dir/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/$stage/$index.log" 2>&1
test ! -e "$out/resources/$stage/$index.time"
set +e
/usr/bin/time -v -o "$out/resources/$stage/$index.time" timeout 3600 apptainer exec --cleanenv --containall \
    --home "$runtime_dir/home:/home/rtc" --pwd /study \
    --bind "$RTC_BUNDLE:/bundle:ro" --bind "$RTC_BUNDLE/study:/study:ro" \
    --bind "$out:/bundle/study/$out_rel:rw" --bind "$out:/study/$out_rel:rw" \
    --bind "$RTC_REPO/harness/tacc_phase2:/phase2:ro" \
    --bind "$runtime_dir/tmp:/tmp:rw" --bind "$runtime_dir/work:/var/tmp:rw" \
    --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
    --env RTC_LAUNCHER_MODULE=launcher/3.10 --env "RTC_NODE_NAME=$(hostname -f)" \
    --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
    "$RTC_IMAGE" /opt/rtc-python/bin/python /phase2/worker_e.py --bundle /bundle --stage "$stage" --index "$index"
status=$?
set -e
if [ "$status" -ne 0 ]; then
    python3 - "$out/STOP.json" "$stage" "$index" "$status" <<'PY'
import json,sys
try:
    with open(sys.argv[1],'x') as f:json.dump({'reason':'repair adapter/container process failed','stage':sys.argv[2],'index':sys.argv[3],'exit_code':sys.argv[4]},f)
except FileExistsError:pass
PY
fi
exit "$status"
