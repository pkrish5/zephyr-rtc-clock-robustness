#!/bin/bash -l
# Storage check task. Same runtime, time/timeout nesting and mounts as
# replay_task.sh (fixture_check.py compares them); runs a probe, never firmware.
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
test "${SLURM_JOB_PARTITION:?}" = development
slot=${1:?slot}
slots=${2:?slots}
primary=${RTC_PRIMARY_BUNDLE:?}
proposal=${RTC_REPLAY_PROPOSAL:?}
out=$RTC_JOB_OUTPUT
rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$primary/plan.json")
index=$slot
limit=1500
runtime=$(mktemp -d "$RTC_NODE_BASE/replay-$index.XXXXXX")
mkdir -p "$runtime/home/.config/renode" "$runtime/tmp" "$runtime/work" \
    "$out/stdout/fixture" "$out/resources/fixture" "$out/processes/fixture"
cp -a "$primary/renode-cache/." "$runtime/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/fixture/$index.log" 2>&1
set +e
/usr/bin/time -v -o "$out/resources/fixture/$index.time" \
  timeout --signal=TERM --kill-after=30s "$limit" \
  apptainer exec --cleanenv --containall --home "$runtime/home:/home/rtc" --pwd /bundle \
  --bind "$primary:/primary:ro" --bind "$primary:/bundle:ro" \
  --bind "$out:/bundle/$rel:rw" --bind "$primary/$rel/builds:/bundle/$rel/builds:ro" \
  --bind "$primary/renode:/renode:ro" \
  --bind "$RTC_REPO/harness/tacc_s2:/sealed-s2:ro" \
  --bind "$RTC_REPO/harness/tacc_s2_evidence:/replay:ro" \
  --bind "$proposal:/replay-proposal.json:ro" \
  --bind "$RTC_REPO/harness/tacc_storage/fixture_probe.py:/fixture_probe.py:ro" \
  --bind "$runtime/tmp:/tmp:rw" --bind "$runtime/work:/var/tmp:rw" \
  --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=${RTC_CONTAINER_SHA256:?}" \
  --env "RTC_REPLAY_PROPOSAL_SHA256=${RTC_REPLAY_PROPOSAL_SHA256:?}" \
  --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \
  --env "RTC_NODE_NAME=$(hostname -f)" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
  "${RTC_IMAGE:?}" /opt/rtc-python/bin/python /fixture_probe.py \
  --proposal /replay-proposal.json --slot "$slot" --slots "$slots" --seconds 1400
status=$?
set -e
echo "fixture task exit $status"
exit "$status"
