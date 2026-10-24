#!/bin/bash -l
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
: "${SLURM_JOB_ID:?}"
test "${SLURM_JOB_PARTITION:-}" = development
index=${1:?task index}
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
phase=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["phase"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/study/$out_rel"
test ! -e "$out/STOP.json"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
mkdir -p "$RTC_BASE/runtime" "$out/resources" "$out/stdout"
runtime_dir=$(mktemp -d "$RTC_BASE/runtime/${SLURM_JOB_ID}-${index}.XXXXXX")
mkdir -p "$runtime_dir/home/.config/renode" "$runtime_dir/tmp" "$runtime_dir/work"
cp -a "$RTC_BUNDLE/renode-cache/." "$runtime_dir/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/$index.log" 2>&1
test ! -e "$out/resources/$index.time"
case "$phase" in AB) worker=worker_ab.py;; D) worker=worker_d.py;; *) exit 2;; esac
set +e
/usr/bin/time -v -o "$out/resources/$index.time" timeout 1500 apptainer exec --cleanenv --containall \
    --home "$runtime_dir/home:/home/rtc" --pwd /study \
    --bind "$RTC_BUNDLE:/bundle:ro" \
    --bind "$RTC_BUNDLE/study:/study:ro" \
    --bind "$out:/bundle/study/$out_rel:rw" \
    --bind "$out:/study/$out_rel:rw" \
    --bind "$RTC_REPO/harness/tacc_phase2:/phase2:ro" \
    --bind "$runtime_dir/tmp:/tmp:rw" --bind "$runtime_dir/work:/var/tmp:rw" \
    --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
    --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
    --env RTC_LAUNCHER_MODULE=launcher/3.10 --env "RTC_NODE_NAME=$(hostname -f)" \
    --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
    "$RTC_IMAGE" /opt/rtc-python/bin/python "/phase2/$worker" --bundle /bundle --index "$index"
status=$?
set -e
if [ "$status" -ne 0 ]; then
    python3 - "$out/STOP.json" "$index" "$status" <<'PY'
import json,sys
try:
    with open(sys.argv[1],'x') as f: json.dump({'reason':'adapter or container process failed','index':sys.argv[2],'exit_code':sys.argv[3]},f)
except FileExistsError: pass
PY
fi
exit "$status"
