#!/bin/bash -l
#SBATCH -J rtc-s2-evidence
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:15:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
: "${RTC_S2_PREVIOUS:?}" "${RTC_S2_EVIDENCE:?}"
python3 "$RTC_REPO/harness/tacc_s2_evidence/collect.py" \
  --bundle "$RTC_BUNDLE" --previous "$RTC_S2_PREVIOUS" \
  --runtime "$RTC_BASE/runtime" --dest "$RTC_S2_EVIDENCE" \
  --slurm-logs "$RTC_BASE/slurm"
