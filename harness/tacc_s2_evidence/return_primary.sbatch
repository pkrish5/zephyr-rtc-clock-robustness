#!/bin/bash -l
#SBATCH -J rtc-s2-return
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:30:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
python3 "$RTC_REPO/harness/tacc_s2_evidence/return_primary.py" \
  --repo "$RTC_REPO" --bundle "$RTC_BUNDLE" --image "$RTC_IMAGE" \
  --dest "${RTC_RETURN_DEST:?}" --slurm-logs "$RTC_BASE/slurm"
