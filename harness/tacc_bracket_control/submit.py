#!/usr/bin/env python3
"""Submit the preregistered development control exactly once."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): digest.update(block)
    return digest.hexdigest()

repo = Path(os.environ['WORK']) / 'zephyr-rtc-clock-robustness'
packet = repo / 'notes/course_improvement_2026-11-12_v1/packet'
execution = packet / 'execution.json'
digest = sha(execution)
assert digest == (packet / 'execution.sha256').read_text().split()[0]
e = json.loads(execution.read_text())
assert e['account'] == 'CCR26073' and e['reservation_su_ceiling'] == 1.0
base = repo / 'tacc_work/20261112-bracket-control-v1'
base.mkdir(exist_ok=True)
logs = Path(os.environ['SCRATCH']) / 'zephyr-rtc-clock-robustness/bracket-control-20261112-v1/slurm'
logs.mkdir(parents=True, exist_ok=True)
image = repo / e['image_relative']
assert sha(image) == e['image_sha256']
values = dict(RTC_REPO=str(repo), RTC_BRACKET_PACKET=str(packet),
              RTC_PRIMARY_BUNDLE=str(repo/e['original_bundle_relative']), RTC_IMAGE=str(image))
cmd = ['sbatch','--parsable','-A','CCR26073','-p','development','-N','1','-n','128','-t','01:00:00',
       '--chdir='+str(repo),'--output='+str(logs/'bracket-%j.out'),'--error='+str(logs/'bracket-%j.err'),
       '--export=ALL,'+','.join(k+'='+v for k,v in values.items()),str(repo/'harness/tacc_bracket_control/job.sbatch')]
with (base/'submission.intent.json').open('x') as f:
    json.dump(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=digest),f)
record = dict(state='uncertain',command=cmd,account='CCR26073',ceiling_su=1.0,planned_processes=11)
try:
    result = subprocess.run(cmd,text=True,capture_output=True,timeout=75)
    record.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
    ids = re.findall(r'^([0-9]+)(?:;[^\n]*)?$',result.stdout,re.M)
    record['state'] = 'accepted' if result.returncode == 0 and len(ids) == 1 else 'rejected_or_uncertain'
    if record['state'] == 'accepted': record['job_id'] = ids[0]
except subprocess.TimeoutExpired:
    record['error'] = 'submission timed out; inspect queue before any retry'
with (base/'submission.json').open('x') as f:
    json.dump(record,f,indent=2); f.write('\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['state']=='accepted' else 2)
