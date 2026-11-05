#!/bin/bash -l
#SBATCH -J rtc-counter-recovery
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_RECOVERY_GROUP:?}" "${RTC_RECOVERY_APPROVAL:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" "counter-recovery-$RTC_RECOVERY_GROUP" \
 python3 "$RTC_REPO/notes/counter_repair_execution_2026-11-05_v1/coordinator.py"
