#!/usr/bin/env python3
"""Submit approved recovery infrastructure commands without new WORK files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--tag',required=True)
parser.add_argument('--receipt',type=Path,required=True)
parser.add_argument('--afterok',type=int)
parser.add_argument('--minutes',type=int,choices=(30,60,120),default=30)
args=parser.parse_args()
if not all(c.isalnum() or c=='-' for c in args.tag+args.name):
    raise SystemExit('Use plain job identifiers')
source=args.source.read_text()
digest=hashlib.sha256(source.encode()).hexdigest()
control='''import json,os,re,subprocess,sys
from pathlib import Path
source='''+repr(source)+'''
digest='''+repr(digest)+'''
tag='''+repr(args.tag)+'''
name='''+repr(args.name)+'''
dependency='''+repr(args.afterok)+'''
walltime='''+repr(f'{args.minutes//60:02d}:{args.minutes%60:02d}:00')+'''
base=Path(os.environ['SCRATCH']).resolve()/'zephyr-rtc-clock-robustness'/tag
base.mkdir(parents=True,exist_ok=False)
script='#!/bin/bash -l\\n#SBATCH -J '+name+'\\n#SBATCH -A TRA25006\\n#SBATCH -p development\\n#SBATCH -N 1\\n#SBATCH -n 128\\n#SBATCH -t '+walltime+'\\n#SBATCH --no-requeue\\nset -euo pipefail\\nexport TMPDIR=/tmp\\npython3 - <<\\'RTC_RECOVERY_COMMAND\\'\\n'+source+'\\nRTC_RECOVERY_COMMAND\\n'
with (base/'job.sbatch').open('x') as f:f.write(script)
env=dict(os.environ,TMPDIR='/tmp',RTC_RECOVERY_REPORT=str(base/'report'),RTC_RECOVERY_SOURCE_SHA256=digest)
command=['sbatch','--parsable','-A','TRA25006','-p','development','--export=ALL','--chdir='+str(base),'--output='+str(base/'job-%j.out'),'--error='+str(base/'job-%j.err'),str(base/'job.sbatch')]
if dependency:command.insert(1,'--dependency=afterok:'+str(dependency))
receipt=dict(source_sha256=digest,tag=tag,command=command,report=str(base/'report'),allocation='TRA25006',queue='development',nodes=1,walltime=walltime,new_builds=0,new_simulations=0)
with (base/'submission-attempt.json').open('x') as f:json.dump(receipt,f,indent=2)
p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90)
ids=re.findall(r'(?m)^(\\d+)(?:;[^\\n]+)?\\s*$',p.stdout)
receipt.update(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,job_id=ids[0] if len(ids)==1 else None)
with (base/'submission.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\\n')
print(json.dumps(receipt,indent=2))
if p.returncode or len(ids)!=1:sys.exit(2)
'''
try:
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=1','ls6','python3 -'],input=control,capture_output=True,text=True,timeout=120)
except subprocess.TimeoutExpired:
    uncertain=dict(tag=args.tag,source_sha256=digest,job_id=None,submission_state='unknown',
        client_error='SSH subprocess timed out after 120 seconds',
        remote_receipt_suffix='/zephyr-rtc-clock-robustness/'+args.tag+'/submission.json',
        do_not_resubmit_until_reconciled=True)
    with args.receipt.open('x') as f:json.dump(uncertain,f,indent=2);f.write('\n')
    print(json.dumps(uncertain,indent=2))
    sys.exit(3)
print(result.stdout)
print(result.stderr,file=sys.stderr)
if result.stdout:
    try:receipt=json.loads(result.stdout)
    except json.JSONDecodeError:receipt=None
    if receipt is not None:
        with args.receipt.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
sys.exit(result.returncode)
