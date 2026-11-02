#!/bin/bash -l
#SBATCH -J rtc-e-resume
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 03:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_IMAGE:?}" "${RTC_E_CHUNK:?}"
: "${RTC_E_RESUME_MANIFEST_SHA256:?}" "${RTC_E_RESUME_PLAN_SHA256:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
printf -v label 'e-resume-%02d' "$RTC_E_CHUNK"
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" "$label" bash -l -c '
set -euo pipefail
python3 "$RTC_REPO/harness/tacc_e_resume/setup_resume.py"
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_JOB_OUTPUT/launcher"
export LAUNCHER_JOB_FILE="$LAUNCHER_WORKDIR/jobfile"
export LAUNCHER_LOGFILE="$LAUNCHER_WORKDIR/launcher.log"
cd "$LAUNCHER_WORKDIR"
set +e
"$LAUNCHER_DIR/paramrun"
launcher_status=$?
set -e
python3 "$RTC_REPO/harness/tacc_e_resume/check_chunk.py"
test "$launcher_status" = 0
'
