#!/bin/bash -l
# New output/mount adapter; the sealed E evaluator and stimuli stay unchanged.
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
test "${SLURM_JOB_PARTITION:?}" = normal
index=${1:?evaluation index}
primary=$RTC_REPO/tacc_work/20261024-repair-v1/e-bundle
rel=results/tacc_phase2_e_20261024_v1
old=$primary/study/$rel
out=$RTC_JOB_OUTPUT
runtime=$(mktemp -d "$RTC_NODE_BASE/resume-$index.XXXXXX")
mkdir -p "$runtime/home/.config/renode" "$runtime/tmp" "$runtime/work"
cp -a "$primary/renode-cache/." "$runtime/home/.config/renode/"
set -o noclobber
exec > "$out/stdout/evaluate/$index.log" 2>&1
set +e
/usr/bin/time -v -o "$out/resources/evaluate/$index.time" \
  timeout --signal=TERM --kill-after=30s 3600 \
  apptainer exec --cleanenv --containall --home "$runtime/home:/home/rtc" --pwd /study \
  --bind "$primary:/original:ro" --bind "$primary:/bundle:ro" --bind "$primary/study:/study:ro" \
  --bind "$out:/bundle/study/$rel:rw" --bind "$out:/study/$rel:rw" \
  --bind "$old/builds:/bundle/study/$rel/builds:ro" --bind "$old/builds:/study/$rel/builds:ro" \
  --bind "$old/execution.json:/bundle/study/$rel/execution.json:ro" \
  --bind "$old/execution.json:/study/$rel/execution.json:ro" \
  --bind "$old/execution.sha256:/bundle/study/$rel/execution.sha256:ro" \
  --bind "$old/execution.sha256:/study/$rel/execution.sha256:ro" \
  --bind "$old/tasks-evaluate.json:/bundle/study/$rel/tasks-evaluate.json:ro" \
  --bind "$old/tasks-evaluate.json:/study/$rel/tasks-evaluate.json:ro" \
  --bind "$old/tasks-controls.json:/bundle/study/$rel/tasks-controls.json:ro" \
  --bind "$old/tasks-controls.json:/study/$rel/tasks-controls.json:ro" \
  --bind "$RTC_REPO/harness/tacc_phase2:/phase2:ro" \
  --bind "$RTC_REPO/harness/tacc_e_resume:/recovery:ro" \
  --bind "$RTC_REPO/notes/e_resume_2026-11-02_v1/packet:/recovery-packet:ro" \
  --bind "$runtime/tmp:/tmp:rw" --bind "$runtime/work:/var/tmp:rw" \
  --env XDG_CACHE_HOME=/var/tmp --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" \
  --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" --env RTC_LAUNCHER_MODULE=launcher/3.10 \
  --env "RTC_NODE_NAME=$(hostname -f)" --env "RTC_E_RESUME_PLAN_SHA256=$RTC_E_RESUME_PLAN_SHA256" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --env "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION" \
  "$RTC_IMAGE" /opt/rtc-python/bin/python /recovery/guarded_worker.py "$index" "$RTC_E_CHUNK"
status=$?
set -e
python3 - "$out/processes/evaluate/$index.json" "$status" "$index" "$RTC_E_CHUNK" "$out/STOP.json" <<'PYCODE'
import json,os,sys
record=dict(exit_code=int(sys.argv[2]),index=int(sys.argv[3]),chunk_id=int(sys.argv[4]),slurm_job_id=os.environ['SLURM_JOB_ID'])
with open(sys.argv[1],'x') as f:
    json.dump(record,f,indent=2);f.write('\n')
if record['exit_code']:
    try:
        with open(sys.argv[5],'x') as f:
            json.dump(dict(reason='recovery container/guard process failed; stop remaining tasks',**record),f,indent=2)
            f.write('\n')
    except FileExistsError:pass
PYCODE
exit "$status"
