#!/bin/bash -l
#SBATCH -J rtc-repairs-cache
#SBATCH -A TRA25006
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 04:00:00
#SBATCH --no-requeue
set -euo pipefail
source "${RTC_REPO:?}/harness/tacc_phase1/common.sh"
# Apptainer's explicit container environment takes precedence with --cleanenv.
# The original task wrapper binds each private WORK runtime/work to /var/tmp.
# Only compiler-capability cache placement changes; all simulation/build
# commands, original sources, frozen ELFs, forecasts and SIF bytes stay fixed.
export APPTAINERENV_XDG_CACHE_HOME=/var/tmp
python3 - "$RTC_BUNDLE" <<'PY'
import json,os,sys
from pathlib import Path
bundle=Path(sys.argv[1])
p=json.loads((bundle/'plan.json').read_text())
out=bundle/'study'/p['output_relative']
with (out/('cache_environment_'+os.environ['SLURM_JOB_ID']+'.json')).open('x') as f:
    json.dump(dict(container_xdg_cache_home='/var/tmp',
                   backing='existing private WORK runtime/work bind for each task',
                   slurm_job_id=os.environ['SLURM_JOB_ID'],
                   scope='cache-path packaging only; no source/ELF/harness changes'),f,indent=2)
PY
exec bash -l "$RTC_REPO/harness/tacc_phase2/packed_e.sbatch"
