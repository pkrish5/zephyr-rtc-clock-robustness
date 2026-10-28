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
python3 "$RTC_REPO/harness/tacc_s2_evidence/stage_audit_paths.py" \
  --repo "$RTC_REPO" \
  --cache "$RTC_REPO/harness/tacc_s2_evidence/protected_inputs_20261024_v1" \
  --out "${RTC_STAGE_RECEIPT:?}"
# Run the original collector wrapper verbatim after its missing paths exist.
bash "$RTC_REPO/harness/tacc_s2_evidence/return_primary.sbatch"
