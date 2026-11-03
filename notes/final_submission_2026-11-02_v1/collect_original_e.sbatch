#!/bin/bash -l
#SBATCH -J rtc-e-original
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" e-original-evidence \
  python3 "$RTC_REPO/notes/final_submission_2026-11-02_v1/collect_original_e.py"
