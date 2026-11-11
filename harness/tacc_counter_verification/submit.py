#!/usr/bin/env python3
"""One development diagnostic job; exclusive intent prevents duplicate runs."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

repo = Path(os.environ['WORK']) / 'zephyr-rtc-clock-robustness'
note = repo / 'notes/counter_verification_2026-11-11_v1'; packet = note / 'packet'
ep = packet/'execution.json'; e = json.loads(ep.read_text())
assert hashlib.sha256(ep.read_bytes()).hexdigest() == (packet/'execution.sha256').read_text().split()[0]
assert e['account'] == 'CCR26073' and e['reservation_su_ceiling'] == 2
base = repo/'tacc_work/20261111-counter-verification-v1'; base.mkdir(exist_ok=True)
logs = Path(os.environ['SCRATCH'])/'zephyr-rtc-clock-robustness/counter-verification-20261111-v1/slurm'
logs.mkdir(parents=True,exist_ok=True)
image = repo/e['image_relative']; assert image.is_file()
assert (image.parent/'rtc-ls6-v1.sif.sha256').read_text().split()[0] == e['image_sha256']
values = dict(RTC_REPO=str(repo),RTC_VERIFY_PACKET=str(packet),RTC_COUNTER_BUNDLE=str(repo/e['original_bundle_relative']),RTC_IMAGE=str(image))
cmd = ['sbatch','--parsable','-A','CCR26073','-p','development','-N','1','-n','128','-t','02:00:00',
       '--chdir='+str(repo),'--output='+str(logs/'diagnostic-%j.out'),'--error='+str(logs/'diagnostic-%j.err'),
       '--export=ALL,'+','.join(k+'='+v for k,v in values.items()),str(repo/'harness/tacc_counter_verification/job.sbatch')]
with (base/'submission.intent.json').open('x') as f:
    json.dump(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=hashlib.sha256(ep.read_bytes()).hexdigest()),f)
record = dict(state='uncertain',command=cmd,account='CCR26073',ceiling_su=2,planned_processes=46)
try:
    result = subprocess.run(cmd,text=True,capture_output=True,timeout=75)
    record.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
    ids = re.findall(r'^([0-9]+)(?:;[^\n]*)?$',result.stdout,re.M)
    if result.returncode==0 and len(ids)==1: record.update(state='accepted',job_id=ids[0])
    else: record['state']='rejected_or_uncertain'
except subprocess.TimeoutExpired:
    record['error']='submission client timed out; inspect receipts/queue; never retry blindly'
with (base/'submission.json').open('x') as f: json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['state']=='accepted' else 2)
