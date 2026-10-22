#!/bin/bash -l
#SBATCH -J rtc-memory-probe
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:20:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?Export RTC_REPO before sbatch}/harness/tacc_phase1/common.sh"
cd "$RTC_BASE"
python3 "$RTC_REPO/harness/tacc_phase1/preflight.py" \
    --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --image "$RTC_IMAGE" \
    --image-record "$RTC_BASE/images/image.json"
bash -l "$RTC_REPO/harness/tacc_phase1/run_task.sh" probe 0
python3 "$RTC_REPO/harness/tacc_phase1/resources.py" probe-report \
    --bundle "$RTC_BUNDLE" \
    --out "$RTC_BUNDLE/study/results/tacc_phase1_20261022_v1/probe/resource_report.json"
echo 'Resource probe complete. Inspect resource_report.json before submitting calibration.'
