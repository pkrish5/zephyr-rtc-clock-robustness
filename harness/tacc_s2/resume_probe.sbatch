#!/bin/bash -l
#SBATCH -J rtc-s2-probe-metadata
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:30:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
test "${SLURM_JOB_PARTITION:?}" = development
: "${RTC_S2_PREVIOUS:?}"
python3 "$RTC_REPO/harness/tacc_s2/control.py" preflight --bundle "$RTC_BUNDLE" --repo "$RTC_REPO" --image "$RTC_IMAGE"
python3 "$RTC_REPO/harness/tacc_s2/control.py" reuse_builds --bundle "$RTC_BUNDLE" --previous "$RTC_S2_PREVIOUS"
probe_index=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["probe_task_index"])' "$RTC_BUNDLE/plan.json")
bash -l "$RTC_REPO/harness/tacc_s2/task.sh" run "$probe_index"
python3 "$RTC_REPO/harness/tacc_s2/control.py" capacity --bundle "$RTC_BUNDLE"
echo 'Metadata-only recovery complete; no source or ELF rebuild. STOP before production.'
