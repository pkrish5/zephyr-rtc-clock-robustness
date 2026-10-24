#!/bin/bash -l
#SBATCH -J rtc-phase2
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 03:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
: "${RTC_CONCURRENCY_CAP:?}"
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/study/$out_rel"
mkdir -p "$out/launcher"
cd "$out/launcher"
python3 "$RTC_REPO/harness/tacc_phase2/preflight.py" --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" \
    --image "$RTC_IMAGE" --cap "$RTC_CONCURRENCY_CAP"
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
        f.write(' '.join(shlex.quote(s) for s in ['bash','-l',sys.argv[2]+'/harness/tacc_phase2/task.sh',str(task['index'])])+'\n')
PY
set +e
"$LAUNCHER_DIR/paramrun"
status=$?
python3 "$RTC_REPO/harness/tacc_phase2/report.py" --bundle "$RTC_BUNDLE" > "$out/report.json"
report_status=$?
set -e
cat "$out/report.json"
test "$status" -eq 0 && test "$report_status" -eq 0
