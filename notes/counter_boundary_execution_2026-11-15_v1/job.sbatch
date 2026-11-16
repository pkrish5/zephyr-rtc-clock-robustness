#!/bin/bash -l
#SBATCH -J rtc-boundary-observer
#SBATCH -A CCR26073
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 01:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_counter_verification/run_packed.sh" boundary-observer \
 python3 "$RTC_REPO/notes/counter_boundary_execution_2026-11-15_v1/coordinator.py"
