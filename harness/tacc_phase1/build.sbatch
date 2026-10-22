#!/bin/bash -l
#SBATCH -J rtc-container-build
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?Export RTC_REPO before sbatch}/harness/tacc_phase1/common.sh"
cd "$RTC_REPO"
bash -l "$RTC_REPO/harness/tacc_phase1/build_image.sh"
