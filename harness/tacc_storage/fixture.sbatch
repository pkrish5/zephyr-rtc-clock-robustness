#!/bin/bash -l
# Compute-node check of the replay storage path. Runs no firmware. A real
# Slurm signal interrupts local Launcher writers, as a walltime limit would.
#SBATCH -J rtc-storage-fixture
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:30:00
#SBATCH --signal=B:USR1@1320
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_PRIMARY_BUNDLE:?}" "${RTC_IMAGE:?}"
: "${RTC_REPLAY_PROPOSAL:?}" "${RTC_REPLAY_PROPOSAL_SHA256:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
source "$RTC_REPO/harness/tacc_storage/runtime.sh"
stamp="$RTC_JOB_BASE/start.stamp"
touch "$stamp"
sleep 2
slots=32
forwarded=0
bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" storage-fixture bash -l -c '
set -euo pipefail
mkdir -p "$RTC_JOB_OUTPUT/builds" "$RTC_JOB_OUTPUT/launcher"
for ((slot=0;slot<32;slot++)); do
    echo "bash -l $RTC_REPO/harness/tacc_storage/fixture_task.sh $slot 32"
done > "$RTC_JOB_OUTPUT/launcher/jobfile"
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_JOB_OUTPUT/launcher"
export LAUNCHER_JOB_FILE="$LAUNCHER_WORKDIR/jobfile"
export LAUNCHER_LOGFILE="$LAUNCHER_WORKDIR/launcher.log"
cd "$LAUNCHER_WORKDIR"
exec "$LAUNCHER_DIR/paramrun"
' &
packed=$!
# The batch shell stays alive to check the result, so it forwards the signal
# that a real replay job's exec'd coordinator would receive directly.
trap 'forwarded=1; kill -USR1 "$packed"' USR1
set +e
wait "$packed"
status=$?
while kill -0 "$packed" 2>/dev/null; do
    wait "$packed"
    status=$?
done
set -e
PYTHONDONTWRITEBYTECODE=1 python3 "$RTC_REPO/harness/tacc_storage/fixture_check.py" \
    --packed-status "$status" --signal-forwarded "$forwarded" --slots "$slots" --stamp "$stamp"
