#!/bin/bash -l
# New replay storage adapter. Never source the historical common.sh.
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
test "${SLURM_JOB_PARTITION:?}" = normal
index=${1:?primary index}
primary=${RTC_PRIMARY_BUNDLE:?}
proposal=${RTC_REPLAY_PROPOSAL:?}
out=$RTC_JOB_OUTPUT
readarray -t values < <(python3 - "$primary/plan.json" "$index" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));i=int(sys.argv[2]);t=next(t for t in p['tasks'] if t['index']==i)
u=next(u for u in p['units'] if u['id']==t['unit_id'])
print(p['output_relative']);print(u['wall_timeout_seconds'])
PY
)
test "${#values[@]}" = 2
rel=${values[0]}
limit=${values[1]}
runtime=$(mktemp -d "$RTC_NODE_BASE/replay-$index.XXXXXX")
mkdir -p "$runtime/home/.config/renode" "$runtime/tmp" "$runtime/work" \
    "$out/stdout/replays" "$out/resources/replays" "$out/processes/replays"
cp -a "$primary/renode-cache/." "$runtime/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/replays/$index.log" 2>&1
set +e
/usr/bin/time -v -o "$out/resources/replays/$index.time" \
  timeout --signal=TERM --kill-after=30s "$limit" \
  apptainer exec --cleanenv --containall --home "$runtime/home:/home/rtc" --pwd /bundle \
  --bind "$primary:/primary:ro" --bind "$primary:/bundle:ro" \
  --bind "$out:/bundle/$rel:rw" --bind "$primary/$rel/builds:/bundle/$rel/builds:ro" \
  --bind "$primary/renode:/renode:ro" \
  --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
  --bind "$RTC_REPO/harness/tacc_s2_evidence:/replay:ro" \
  --bind "$proposal:/replay-proposal.json:ro" \
  --bind "$runtime/tmp:/tmp:rw" --bind "$runtime/work:/var/tmp:rw" \
  --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=${RTC_CONTAINER_SHA256:?}" \
  --env "RTC_REPLAY_PROPOSAL_SHA256=${RTC_REPLAY_PROPOSAL_SHA256:?}" \
  --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
  --env "RTC_NODE_NAME=$(hostname -f)" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
  "${RTC_IMAGE:?}" /opt/rtc-python/bin/python /replay/replay_worker.py \
  --proposal /replay-proposal.json --index "$index"
status=$?
set -e
python3 - "$out/processes/replays/$index.json" "$status" "$index" <<'PY'
import json,os,sys
with open(sys.argv[1],'x') as f:
    json.dump(dict(exit_code=int(sys.argv[2]),primary_index=int(sys.argv[3]),
                   slurm_job_id=os.environ['SLURM_JOB_ID'],purpose='S2 replay, not a replacement primary'),f,indent=2)
    f.write('\n')
PY
exit "$status"
