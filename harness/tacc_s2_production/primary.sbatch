#!/bin/bash -l
#SBATCH -J rtc-s2-primary
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 06:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = normal
python3 "$RTC_REPO/harness/tacc_s2_production/setup.py" --bundle "$RTC_BUNDLE" --previous "${RTC_S2_PREVIOUS:?}" --repo "$RTC_REPO" --image "$RTC_IMAGE"
out_rel=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["output_relative"])' "$RTC_BUNDLE/plan.json")
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1 LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_BUNDLE/$out_rel/launcher/primary" LAUNCHER_JOB_FILE="$RTC_BUNDLE/$out_rel/launcher/primary/jobfile" LAUNCHER_LOGFILE="$RTC_BUNDLE/$out_rel/launcher/primary/launcher.log"
cd "$LAUNCHER_WORKDIR"
"$LAUNCHER_DIR/paramrun"
echo 'Primary schedule finished; outcomes require audit, replay and reference attribution. E2 and paper remain held.'
