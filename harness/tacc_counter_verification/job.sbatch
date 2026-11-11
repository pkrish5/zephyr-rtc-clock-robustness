#!/bin/bash -l
#SBATCH -J rtc-counter-verify
#SBATCH -A CCR26073
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_VERIFY_PACKET:?}" "${RTC_COUNTER_BUNDLE:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_counter_verification/run_packed.sh" counter-diagnostics \
 python3 "$RTC_REPO/harness/tacc_counter_verification/coordinator.py"
