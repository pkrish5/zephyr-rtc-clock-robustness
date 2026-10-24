#!/bin/bash -l
#SBATCH -J rtc-return-ab
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:10:00
#SBATCH --no-requeue
set -euo pipefail
root="$WORK/zephyr-rtc-clock-robustness"
bundle="$root/tacc_work/20261024-phase2/ab-bundle"
dest="$root/tacc_work/20261024-return-v1"
mkdir -p "$dest"
test ! -e "$dest/ab-results.tar.gz"
test ! -e "$dest/ab-verification.json"
python3 - "$bundle" "$root" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[2])/'harness/tacc_phase2'))
from support import verify_inputs
p=verify_inputs(Path(sys.argv[1]),Path(sys.argv[2]))
assert p['phase']=='AB' and len(p['tasks'])==1632
PY
python3 "$root/harness/tacc_phase2/report.py" --bundle "$bundle" > "$dest/ab-verification.json"
cmp -s "$dest/ab-verification.json" "$bundle/study/results/tacc_phase2_ab_20261024_v1/report.json"
tar -czf "$dest/ab-results.tar.gz" -C "$bundle/study/results" tacc_phase2_ab_20261024_v1
sha256sum "$dest/ab-results.tar.gz" > "$dest/ab-results.tar.gz.sha256"
python3 - "$dest" <<'PY'
import json,os,socket,sys
from pathlib import Path
with (Path(sys.argv[1])/'packing.json').open('x') as f:
    json.dump(dict(slurm_job_id=os.environ['SLURM_JOB_ID'],node_name=socket.gethostname(),
                   purpose='Independent raw-hash audit and packaging only; no firmware executions'),f,indent=2)
PY
cat "$dest/ab-results.tar.gz.sha256"
