#!/bin/bash -l
#SBATCH -J rtc-natural-recovery
#SBATCH -A CCR26073
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 36:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_counter_verification/run_packed.sh" natural-recovery \
 python3 "$RTC_REPO/notes/counter_natural_recovery_2026-11-20_v1/coordinator.py"
