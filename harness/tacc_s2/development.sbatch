#!/bin/bash -l
#SBATCH -J rtc-s2-qualify
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 01:30:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
: "${RTC_S2_STAGE:?build_probe or qualification}"
python3 "$RTC_REPO/harness/tacc_s2/control.py" preflight --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --image "$RTC_IMAGE"
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
out="$RTC_BUNDLE/$out_rel"
launch() {
    local phase=$1
    export LAUNCHER_PPN=$2 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1 LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
    unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
    mkdir -p "$out/launcher/$phase"
    export LAUNCHER_WORKDIR="$out/launcher/$phase" LAUNCHER_JOB_FILE="$out/launcher/$phase/jobfile" LAUNCHER_LOGFILE="$out/launcher/$phase/launcher.log"
    python3 "$RTC_REPO/harness/tacc_s2/control.py" jobfile --phase "$phase" --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --out "$LAUNCHER_JOB_FILE"
    cd "$LAUNCHER_WORKDIR"
    if [ -s "$LAUNCHER_JOB_FILE" ]; then
        "$LAUNCHER_DIR/paramrun"
    else
        echo "No qualified tasks for $phase; not-attempted reasons retained."
    fi
}
if [ "$RTC_S2_STAGE" = build_probe ]; then
    launch build 4
    probe_index=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["probe_task_index"])' "$RTC_BUNDLE/plan.json")
    bash -l "$RTC_REPO/harness/tacc_s2/task.sh" run "$probe_index"
    python3 "$RTC_REPO/harness/tacc_s2/control.py" capacity --bundle "$RTC_BUNDLE"
elif [ "$RTC_S2_STAGE" = qualification ]; then
    workers=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["workers"])' "$out/capacity.json")
    launch nominal "$workers"
    launch calibration "$workers"
    python3 "$RTC_REPO/harness/tacc_s2/control.py" report --bundle "$RTC_BUNDLE"
else
    exit 2
fi
echo 'STOP before production. E and E2 untouched.'
