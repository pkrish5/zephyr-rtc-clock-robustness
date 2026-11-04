#!/usr/bin/env python3
"""Lightweight LS6 metadata/submission only. Never retries an accepted/uncertain job."""
import argparse,hashlib,json,os,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--unit',choices=['f4-rtc','f4-counter'],required=True);a=p.parse_args()
root=Path(os.environ['WORK'])/'zephyr-rtc-clock-robustness';packet=root/'notes/fixed_repeatability_2026-11-04_v1/packet';n=json.loads((packet/'plan.json').read_text())
assert hashlib.sha256((packet/'plan.json').read_bytes()).hexdigest()==(packet/'plan.sha256').read_text().split()[0]
base=root/'tacc_work/20261104-fixed-repeatability-v1';base.mkdir(exist_ok=True)
receipt=base/f'submission-{a.unit}.json';intent=base/f'submission-{a.unit}.intent.json'
# Exclusive intent is intentionally never removed, including on timeout.
with intent.open('x') as f:json.dump(dict(unit=a.unit,timestamp_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=hashlib.sha256((packet/'plan.json').read_bytes()).hexdigest()),f,indent=2)
logs=Path(os.environ['SCRATCH'])/'zephyr-rtc-clock-robustness/fixed-repeatability-20261104-v1/slurm';logs.mkdir(parents=True,exist_ok=True)
values=dict(RTC_REPO=str(root),RTC_REPEAT_PACKET=str(packet),RTC_REPEAT_PRIMARY=str(root/'tacc_work/20261026-s2-primary-v1/bundle'),RTC_REPEAT_UNIT=a.unit,RTC_IMAGE=str(root/'tacc_work/20261022-v9/images/rtc-ls6-v1.sif'))
job=n['jobs'][a.unit]
cmd=['sbatch','--parsable','-A','TRA25006','-p','development','-N','1','-n','128','-t',job['wall_limit'],'--job-name=rtc-repeat-'+a.unit,'--chdir='+str(root),'--output='+str(logs/(a.unit+'-%j.out')),'--error='+str(logs/(a.unit+'-%j.err')),'--export=ALL,'+','.join(k+'='+v for k,v in values.items())]
if a.unit=='f4-counter':
 prior=json.loads((base/'submission-f4-rtc.json').read_text());assert prior['state']=='accepted';cmd+=['--dependency=afterany:'+prior['job_id']]
cmd+=[str(root/'harness/tacc_fixed_repeatability/job.sbatch')]
record=dict(state='uncertain',unit=a.unit,command=cmd,estimated_su=job['estimated_node_hours'],reservation_su_ceiling=job['reservation_su_ceiling'],plan_sha256=hashlib.sha256((packet/'plan.json').read_bytes()).hexdigest())
try:
 r=subprocess.run(cmd,text=True,capture_output=True,timeout=75);record.update(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
 ids=re.findall(r'^([0-9]+)(?:;[^\n]*)?$',r.stdout,re.M)
 if r.returncode==0 and len(ids)==1:record.update(state='accepted',job_id=ids[0])
 else:record['state']='rejected_or_uncertain'
except subprocess.TimeoutExpired as e:record.update(error='sbatch client timed out; inspect sacct/squeue before any retry',stdout=str(e.stdout),stderr=str(e.stderr))
with receipt.open('x') as f:json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(record,indent=2));raise SystemExit(0 if record['state']=='accepted' else 2)
