#!/bin/bash -l
# Draft submission wrapper; requires the user's normal-queue approval and
# a sealed roster from independently verified primary evidence.
#SBATCH -J rtc-s2-replays
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 01:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_PRIMARY_BUNDLE:?}" "${RTC_IMAGE:?}"
: "${RTC_REPLAY_PROPOSAL:?}" "${RTC_REPLAY_PROPOSAL_SHA256:?}"
: "${RTC_REPLAY_CODE_MANIFEST:?}" "${RTC_REPLAY_CODE_MANIFEST_SHA256:?}"
: "${RTC_REPLAY_APPROVAL_RECEIPT:?record explicit user approval before submission}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" s2-replays bash -l -c '
set -euo pipefail
python3 "$RTC_REPO/harness/tacc_s2_evidence/setup_replays.py"
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_JOB_OUTPUT/launcher"
export LAUNCHER_JOB_FILE="$LAUNCHER_WORKDIR/jobfile"
export LAUNCHER_LOGFILE="$LAUNCHER_WORKDIR/launcher.log"
cd "$LAUNCHER_WORKDIR"
exec "$LAUNCHER_DIR/paramrun"
'
