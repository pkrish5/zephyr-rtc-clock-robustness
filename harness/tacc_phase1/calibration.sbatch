#!/bin/bash -l
#SBATCH -J rtc-calibration
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 01:30:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?Export RTC_REPO before sbatch}/harness/tacc_phase1/common.sh"
out="$RTC_BUNDLE/study/results/tacc_phase1_20261022_v1"
mkdir -p "$out/calibration/launcher"
cd "$out/calibration/launcher"
python3 "$RTC_REPO/harness/tacc_phase1/preflight.py" \
    --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --image "$RTC_IMAGE" \
    --image-record "$RTC_BASE/images/image.json"
python3 "$RTC_REPO/harness/tacc_phase1/resources.py" capacity \
    --bundle "$RTC_BUNDLE" --cap "$RTC_CONCURRENCY_CAP" \
    --requested-seconds 5400 --out "$out/calibration/concurrency.json"
export LAUNCHER_PPN
LAUNCHER_PPN=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["concurrency_per_node"])' "$out/calibration/concurrency.json")
export LAUNCHER_NHOSTS=1
export LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved
export LAUNCHER_BIND=1
export LAUNCHER_WORKDIR="$out/calibration/launcher"
export LAUNCHER_JOB_FILE="$out/calibration/launcher/jobfile"
export LAUNCHER_LOGFILE="$out/calibration/launcher/launcher.log"
# This is one already-allocated node. Local Launcher mode avoids SSH/MFA
# and the launcher's remote-host retry mechanism. Claims prohibit reruns.
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
python3 - "$RTC_BUNDLE" "$RTC_REPO" "$LAUNCHER_JOB_FILE" <<'PY'
import json,shlex,sys
from pathlib import Path
plan=json.loads((Path(sys.argv[1])/'calibration_plan.json').read_text())
wrapper=Path(sys.argv[2])/'harness/tacc_phase1/run_task.sh'
with Path(sys.argv[3]).open('x') as f:
    for task in plan['tasks']:
        f.write(' '.join(shlex.quote(x) for x in ['bash','-l',str(wrapper),'calibration',str(task['index'])])+'\n')
PY
set +e
"$LAUNCHER_DIR/paramrun"
launcher_status=$?
python3 "$RTC_REPO/harness/tacc_phase1/calibration.py" compare \
    --bundle "$RTC_BUNDLE" > "$out/calibration_report.json"
comparison_status=$?
set -e
cat "$out/calibration_report.json"
test "$launcher_status" -eq 0 && test "$comparison_status" -eq 0
echo 'STOP: send the calibration report and records back for review; no production submission.'
