#!/usr/bin/env python3
import hashlib,json,os,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
r=Path(os.environ['WORK'])/'zephyr-rtc-clock-robustness';n=r/'notes/counter_boundary_execution_2026-11-15_v1';ep=n/'execution.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads(ep.read_text());assert sha(ep)==(n/'execution.sha256').read_text().split()[0]
assert e['stage_reservation_su']==1 and e['total_study_ceiling_su']==10
for rel,h in e['code_sha256'].items():assert sha(r/rel)==h,rel
assert sha(n/'PROTOCOL.md')==e['protocol_sha256']
# Small original execution-code check on login node; full seals on compute.
for rel,h in e['active_counter_inputs_sha256'].items():
 if rel.startswith('harness/tacc_counter_repair/'):assert sha(r/rel)==h,rel
base=r/'tacc_work/20261115-boundary-observer-v1';base.mkdir(exist_ok=True)
assert not (base/'submission.json').exists() and not (base/'submission.intent.json').exists()
image=r/e['image_relative'];assert image.is_file()
assert (image.parent/'rtc-ls6-v1.sif.sha256').read_text().split()[0]==e['image_sha256']
logs=Path(os.environ['SCRATCH'])/'zephyr-rtc-clock-robustness/boundary-observer-20261115-v1/slurm';logs.mkdir(parents=True,exist_ok=True)
cmd=['sbatch','--parsable','-A','CCR26073','-p','development','-N','1','-n','128','-t','01:00:00','--chdir='+str(r),'--output='+str(logs/'observer-%j.out'),'--error='+str(logs/'observer-%j.err'),'--export=ALL,RTC_REPO='+str(r)+',RTC_IMAGE='+str(image),str(n/'job.sbatch')]
with (base/'submission.intent.json').open('x') as f:json.dump({'time':datetime.now(timezone.utc).isoformat(),'execution_sha256':sha(ep),'command':cmd},f)
record={'state':'uncertain','command':cmd,'reservation_su':1,'study_ceiling_su':10}
try:
 x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);record.update(returncode=x.returncode,stdout=x.stdout,stderr=x.stderr)
 ids=re.findall(r'^([0-9]+)(?:;[^\n]*)?$',x.stdout,re.M)
 if x.returncode==0 and len(ids)==1:record.update(state='accepted',job_id=ids[0])
 else:record['state']='rejected_or_uncertain'
except subprocess.TimeoutExpired:record['error']='timeout: inspect intent/Slurm; never retry'
with (base/'submission.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['state']=='accepted' else 2)
