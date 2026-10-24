#!/bin/bash -l
#SBATCH -J rtc-d-cache-dev
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
: "${RTC_CONCURRENCY_CAP:?}"
# /var/tmp is the existing per-task WORK-backed bind. No image/source edits.
export APPTAINERENV_XDG_CACHE_HOME=/var/tmp
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/study/$out_rel"
mkdir -p "$out/launcher"
cd "$out/launcher"
python3 "$RTC_REPO/harness/tacc_phase2/preflight.py" --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" \
    --image "$RTC_IMAGE" --cap "$RTC_CONCURRENCY_CAP"
# Validate the cache fix on the first planned control before packing the rest.
# This is task 0's only execution, not an extra/retried nominal score.
bash -l "$RTC_REPO/harness/tacc_phase2/task_d_cache_dev.sh" 0
python3 - "$out" <<'PY_SMOKE'
import json,sys
from pathlib import Path
out=Path(sys.argv[1])
b=json.loads((out/'build_records/0000.json').read_text())
rows=[json.loads(p.read_text()) for p in (out/'records').glob('*.json')]
assert b['status']=='pass' and len(rows)==1 and rows[0]['task_index']==0 and rows[0]['outcome']=='pass', 'Cache smoke control failed; stop before remaining 215 tasks'
print('First control built and passed with WORK-backed XDG cache')
PY_SMOKE
export LAUNCHER_PPN
LAUNCHER_PPN=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["concurrency"])' "$out/capacity.json")
export LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1 LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
export LAUNCHER_WORKDIR="$out/launcher" LAUNCHER_JOB_FILE="$out/launcher/jobfile" LAUNCHER_LOGFILE="$out/launcher/launcher.log"
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
python3 - "$RTC_BUNDLE" "$RTC_REPO" "$LAUNCHER_JOB_FILE" <<'PY'
import json,shlex,sys
from pathlib import Path
plan=json.loads((Path(sys.argv[1])/'plan.json').read_text())
with Path(sys.argv[3]).open('x') as f:
    for task in plan['tasks']:
        if task['index']==0: continue  # already validated once above
        f.write(' '.join(shlex.quote(s) for s in ['bash','-l',sys.argv[2]+'/harness/tacc_phase2/task_d_cache_dev.sh',str(task['index'])])+'\n')
PY
set +e
"$LAUNCHER_DIR/paramrun"
status=$?
python3 "$RTC_REPO/harness/tacc_phase2/report.py" --bundle "$RTC_BUNDLE" > "$out/report.json"
report_status=$?
set -e
cat "$out/report.json"
test "$status" -eq 0 && test "$report_status" -eq 0

python3 - "$out/report.json" <<'PY_CHECK'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['complete'] and r['outcomes']=={'pass':216} and r['build_outcomes']=={'pass':216}, 'Disabled controls not all passing; retain results and STOP'
print('D cache-path retry validated: 216 builds and 216 nominal passes')
PY_CHECK
