#!/bin/bash -l
#SBATCH -J rtc-return-d
#SBATCH -A TRA25006
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 00:10:00
#SBATCH --no-requeue
set -euo pipefail
root="$WORK/zephyr-rtc-clock-robustness"
bundle="$root/tacc_work/20261024-d-cache-v2/d-cache-v2-bundle"
dest="$root/tacc_work/20261024-return-d-v1"
mkdir -p "$dest"
test ! -e "$dest/d-evidence.tar.gz"
python3 "$root/harness/tacc_phase2/report.py" --bundle "$bundle" > "$dest/report.json"
cmp -s "$dest/report.json" "$bundle/study/results/tacc_phase2_d_20261024_v2/report.json"
python3 "$root/harness/tacc_phase2/summarize_d.py" --bundle "$bundle" > "$dest/breakdown.json"
python3 - "$root" "$bundle" "$dest" <<'PY'
import json,os,socket,sys,tarfile
from pathlib import Path
root,bundle,dest=map(Path,sys.argv[1:])
sys.path.insert(0,str(root/'harness/tacc_phase2'))
from support import read,save,sha,verify_inputs
p=verify_inputs(bundle,root)
out=bundle/'study'/p['output_relative']
r=read(dest/'report.json')
assert r['complete'] and r['outcomes']=={'pass':216} and r['build_outcomes']=={'pass':216}
builds=[read(f) for f in (out/'build_records').glob('*.json')]
assert len(builds)==216
for b in builds:
    for field in ('elf','log'):
        assert sha(bundle/'study'/b[field+'_path'])==b[field+'_sha256']
files=[]
for f in out.rglob('*'):
    if not f.is_file():continue
    rel=f.relative_to(out)
    # Retain all raw scientific outputs and build evidence. Large compiler
    # intermediates and ELFs stay immutable remotely, with verified hashes.
    if rel.parts[0]=='builds' and not (len(rel.parts)==3 and rel.parts[-1]=='build.log') and 'app' not in rel.parts:
        continue
    files.append(f)
with tarfile.open(dest/'d-evidence.tar.gz','w:gz') as tar:
    for f in sorted(files):
        assert not f.is_symlink()
        tar.add(f,arcname=str(Path(out.name)/f.relative_to(out)),recursive=False)
save(dest/'packing.json',dict(slurm_job_id=os.environ['SLURM_JOB_ID'],node_name=socket.gethostname(),
    archive_sha256=sha(dest/'d-evidence.tar.gz'),archive_files=len(files),
    build_elf_and_log_hashes_verified=len(builds),
    omitted='Compiler intermediates and ELFs remain immutable at the original WORK result prefix; ELF hashes verified on compute',
    purpose='Read-only evidence verification and packaging; no firmware executions'))
print((dest/'d-evidence.tar.gz').stat().st_size,'bytes',sha(dest/'d-evidence.tar.gz'))
PY
