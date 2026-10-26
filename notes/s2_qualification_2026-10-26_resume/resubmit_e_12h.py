#!/usr/bin/env python3
"""User-authorized replacement of a never-started E job; no experiment logic changes."""
import hashlib,json,os,re,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
root=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
assert Path.cwd().resolve()==root
oldid='3532543';base=root/'tacc_work/20261024-repair-v1';bundle=base/'e-bundle'
p=json.loads((bundle/'plan.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(bundle/'plan.json')=='2c9317ea293b72a4cbf1e7779f22ceecdbf5f3a835559db35e4114a1a95971b6'
assert sha(bundle/'plan.json')==(bundle/'plan.sha256').read_text().split()[0]
out=bundle/'study'/p['output_relative']
def run(cmd):return subprocess.run(cmd,capture_output=True,text=True)
def info():
 r=run(['scontrol','show','job','-o',oldid]);assert r.returncode==0,r.stderr;return r.stdout
before=info()
if 'JobState=PENDING' not in before:
 print(json.dumps(dict(replaced=False,reason='original is no longer pending; left unchanged',original=before)));raise SystemExit(0)
assert 'Account=TRA25006' in before and 'RunTime=00:00:00' in before
for rel in ['controls/records','faults/records','legal/records','launcher/controls','launcher/evaluate']:
 q=out/rel;assert not q.exists(),str(q)+' already exists; stop to avoid duplication'
gate=run(['sacct','-nXP','-j','3532542','--format=JobIDRaw,State,ExitCode']);assert gate.returncode==0
assert any(line.startswith('3532542|COMPLETED|0:0') for line in gate.stdout.splitlines()),gate.stdout
folder=root/'tacc_work/20261026-e-resubmit-v1';folder.mkdir(parents=True,exist_ok=False)
def save(name,x):
 with (folder/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
metadata={str(f.relative_to(bundle)):sha(f) for f in [bundle/'plan.json',out/'execution.json',out/'execution.sha256',out/'tasks-controls.json',out/'tasks-evaluate.json']}
save('before.json',dict(original_job=oldid,slurm=before,completed_gate=gate.stdout,metadata_sha256=metadata,
 expected_su=8,reservation_ceiling_su=12,requested_limit='12:00:00',timestamp_utc=datetime.now(timezone.utc).isoformat()))
hold=run(['scontrol','hold',oldid]);save('hold.json',dict(returncode=hold.returncode,stdout=hold.stdout,stderr=hold.stderr));assert hold.returncode==0,hold.stderr
assert 'JobState=PENDING' in info(),'Original started; stop without cancellation/replacement'
cancel=run(['scancel','--state=PENDING',oldid]);save('cancel.json',dict(returncode=cancel.returncode,stdout=cancel.stdout,stderr=cancel.stderr));assert cancel.returncode==0,cancel.stderr
cancelled=info();save('cancelled_state.json',dict(slurm=cancelled))
assert 'JobState=CANCELLED' in cancelled and 'RunTime=00:00:00' in cancelled,cancelled
for rel,d in metadata.items():assert sha(bundle/rel)==d,rel
image=root/'tacc_work/20261023-v10/images/rtc-ls6-v1.sif'
env=dict(os.environ,RTC_REPO=str(root),RTC_BASE=str(base),RTC_BUNDLE=str(bundle),
 RTC_D_BUNDLE=str(root/'tacc_work/20261024-d-cache-v2/d-cache-v2-bundle'),RTC_IMAGE=str(image),RTC_E_STAGE='evaluate')
cmd=['sbatch','--parsable','-A','TRA25006','-p','normal','-N','1','-n','128','-t','12:00:00','-J','rtc-repair-eval12',
 '--output='+str(base/'logs/evaluate12h-%j.out'),'--error='+str(base/'logs/evaluate12h-%j.err'),str(root/'harness/tacc_phase2/packed_e_cache.sbatch')]
sent=subprocess.run(cmd,capture_output=True,text=True,env=env)
ids=[s for s in sent.stdout.splitlines() if re.fullmatch(r'\d+(;[^\s]+)?',s.strip())]
receipt=dict(returncode=sent.returncode,stdout=sent.stdout,stderr=sent.stderr,command=cmd,
 replaced_job=oldid,job_id=ids[-1].split(';')[0] if ids else None,partition='normal',account='TRA25006',nodes=1,
 wall_limit='12:00:00',estimated_su=8,reservation_ceiling_su=12,metadata_sha256=metadata,
 no_rebuilds=True,no_nominal_reruns=True,completed_gate='3532542',E2_started=False,
 timestamp_utc=datetime.now(timezone.utc).isoformat())
save('submission.json',receipt);assert sent.returncode==0 and receipt['job_id'],receipt
for rel,d in metadata.items():assert sha(bundle/rel)==d,rel
print(json.dumps(receipt))
