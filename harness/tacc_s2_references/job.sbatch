#!/bin/bash -l
#SBATCH -J rtc-s2-reference
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_PRIMARY_BUNDLE:?}" "${RTC_IMAGE:?}"
: "${RTC_REFERENCE_PACKET:?}" "${RTC_REFERENCE_PLAN_SHA256:?}" "${RTC_REFERENCE_CODE_SHA256:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" s2-reference bash -l -c '
set -euo pipefail
python3 "$RTC_REPO/harness/tacc_s2_references/driver.py" setup
python3 - <<"PY"
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess
from pathlib import Path
repo=Path(os.environ["RTC_REPO"])
plan=json.load(open(Path(os.environ["RTC_JOB_BASE"])/"reference-bundle/plan.json"))
def build(unit):
    return subprocess.run(["bash","-l",str(repo/"harness/tacc_s2_references/task.sh"),"build",unit["id"]]).returncode
with ThreadPoolExecutor(max_workers=4) as pool:
    codes=list(pool.map(build,plan["units"]))
if any(codes): raise SystemExit("Reference build failed; no reference execution")
PY
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
for phase in qualification evaluation; do
    export LAUNCHER_WORKDIR="$RTC_JOB_OUTPUT/launcher/$phase"
    export LAUNCHER_JOB_FILE="$LAUNCHER_WORKDIR/jobfile"
    export LAUNCHER_LOGFILE="$LAUNCHER_WORKDIR/launcher.log"
    cd "$LAUNCHER_WORKDIR"
    "$LAUNCHER_DIR/paramrun"
    python3 "$RTC_REPO/harness/tacc_s2_references/driver.py" "audit-$phase"
done
'
