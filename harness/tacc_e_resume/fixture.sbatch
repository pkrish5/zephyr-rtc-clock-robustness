#!/bin/bash -l
#SBATCH -J rtc-e-storage
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 02:00:00
#SBATCH --signal=B:USR1@600
#SBATCH --no-requeue
set -euo pipefail
: "${RTC_REPO:?}" "${RTC_IMAGE:?}" "${RTC_E_FIXTURE_MANIFEST_SHA256:?}"
export RTC_CONTAINER_SHA256=94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1
exec bash "$RTC_REPO/harness/tacc_storage/run_packed.sh" e-storage-fixture bash -l -c '
set -euo pipefail
python3 "$RTC_REPO/harness/tacc_e_resume/setup_fixture.py"
export LAUNCHER_PPN=32 LAUNCHER_NHOSTS=1 LAUNCHER_LOCALHOST=1
export LAUNCHER_SCHED=interleaved LAUNCHER_BIND=1
unset LAUNCHER_RMI LAUNCHER_HOSTFILE LAUNCHER_RMI_HOSTFILE
export LAUNCHER_WORKDIR="$RTC_JOB_OUTPUT/launcher"
export LAUNCHER_JOB_FILE="$LAUNCHER_WORKDIR/jobfile"
export LAUNCHER_LOGFILE="$LAUNCHER_WORKDIR/launcher.log"
cd "$LAUNCHER_WORKDIR"
"$LAUNCHER_DIR/paramrun"
python3 - <<'"'"'PY'"'"'
import json,os
from pathlib import Path
out=Path(os.environ["RTC_JOB_OUTPUT"])
setup=json.loads((out/"job_metadata/fixture_setup.json").read_text())
records=list((out/"fixture").glob("*.json"))
assert {json.loads(p.read_text())["index"] for p in records}==set(setup["fixture_indices"])
assert all(json.loads(p.read_text())["all_mount_checks_passed"] for p in records)
with (out/"job_metadata/fixture_result.json").open("x") as f:
    json.dump(dict(all_passed=True,container_mount_probes=len(records),new_simulations=0,new_builds=0),f,indent=2)
    f.write("\n")
PY
'
