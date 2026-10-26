#!/bin/bash -l
#SBATCH -J rtc-s2-calibration
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
python3 "$RTC_REPO/harness/tacc_s2/control.py" preflight --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --image "$RTC_IMAGE"
python3 "$RTC_REPO/harness/tacc_s2/control.py" reuse_builds --bundle "$RTC_BUNDLE" --previous "${RTC_S2_PREVIOUS:?}"
python3 "$RTC_REPO/harness/tacc_s2_followup/manage.py" jobfile --bundle "$RTC_BUNDLE" --repo "$RTC_REPO"
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
export LAUNCHER_PPN=15 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1 LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_BUNDLE/$out_rel/launcher/resume" LAUNCHER_JOB_FILE="$RTC_BUNDLE/$out_rel/launcher/resume/jobfile" LAUNCHER_LOGFILE="$RTC_BUNDLE/$out_rel/launcher/resume/launcher.log"
cd "$LAUNCHER_WORKDIR"
"$LAUNCHER_DIR/paramrun"
python3 "$RTC_REPO/harness/tacc_s2_followup/manage.py" report --bundle "$RTC_BUNDLE" --repo "$RTC_REPO"
python3 "$RTC_REPO/harness/tacc_s2_followup/manage.py" archive --bundle "$RTC_BUNDLE" --repo "$RTC_REPO"
echo 'Calibration continuation finished. No production submission by this job.'
