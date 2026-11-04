#!/bin/bash -l
#SBATCH -J rtc-fixed-repeat
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@600
set -euo pipefail
: "${RTC_REPEAT_UNIT:?}" "${RTC_REPEAT_PACKET:?}" "${RTC_REPEAT_PRIMARY:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" "fixed-repeat-${RTC_REPEAT_UNIT}" \
 python3 "$RTC_REPO/harness/tacc_fixed_repeatability/coordinator.py"
