#!/bin/bash -l
#SBATCH -J rtc-repairs
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 04:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
: "${RTC_E_STAGE:?gates or evaluate}" "${RTC_D_BUNDLE:?}"
case "$RTC_E_STAGE" in gates|evaluate);; *) exit 2;; esac
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/study/$out_rel"
python3 "$RTC_REPO/harness/tacc_phase2/preflight_e.py" --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" \
    --image "$RTC_IMAGE" --stage "$RTC_E_STAGE" --d-bundle "$RTC_D_BUNDLE"
export LAUNCHER_PPN
LAUNCHER_PPN=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["concurrency"])' "$out/capacity-$RTC_E_STAGE.json")
export LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1 LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
launch_stage() {
    local phase=$1
    mkdir -p "$out/launcher/$phase"
    cd "$out/launcher/$phase"
    export LAUNCHER_WORKDIR="$out/launcher/$phase" LAUNCHER_JOB_FILE="$out/launcher/$phase/jobfile" LAUNCHER_LOGFILE="$out/launcher/$phase/launcher.log"
    python3 - "$RTC_BUNDLE" "$RTC_REPO" "$phase" "$LAUNCHER_JOB_FILE" <<'PY'
import json,shlex,sys
from pathlib import Path
bundle,repo,phase,dst=sys.argv[1:]
p=json.loads((Path(bundle)/'plan.json').read_text())
out=Path(bundle)/'study'/p['output_relative']
tasks=p['tasks'] if phase=='gates' else json.loads((out/('tasks-'+phase+'.json')).read_text())
with open(dst,'x') as f:
    for t in tasks:
        f.write(' '.join(shlex.quote(s) for s in ['bash','-l',repo+'/harness/tacc_phase2/task_e.sh',phase,str(t['index'])])+'\n')
PY
    "$LAUNCHER_DIR/paramrun"
    test ! -e "$out/STOP.json"
}
if [ "$RTC_E_STAGE" = gates ]; then
    launch_stage gates
    python3 "$RTC_REPO/harness/tacc_phase2/finalize_e.py" seal --bundle "$RTC_BUNDLE"
else
    launch_stage controls
    python3 "$RTC_REPO/harness/tacc_phase2/finalize_e.py" controls --bundle "$RTC_BUNDLE"
    launch_stage evaluate
    python3 "$RTC_REPO/harness/tacc_phase2/finalize_e.py" report --bundle "$RTC_BUNDLE"
    echo 'STOP at Phase 3: before/after number table required before paper edits. E2 remains on hold.'
fi
