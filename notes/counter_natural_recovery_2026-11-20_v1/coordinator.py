#!/usr/bin/env python3
import hashlib,json,os,shlex,shutil,subprocess,time
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
r=Path(os.environ['RTC_REPO']);n=r/'notes/counter_natural_recovery_2026-11-20_v1';e=json.loads((n/'execution.json').read_text())
assert sha(n/'execution.json')==(n/'execution.sha256').read_text().split()[0]
assert os.environ['SLURM_JOB_ACCOUNT'].upper()=='CCR26073' and os.environ['SLURM_JOB_PARTITION']=='normal'
original=r/e['original_bundle_relative'];out=Path(os.environ['RTC_JOB_OUTPUT']);b=Path(os.environ['RTC_JOB_BASE'])/'natural-bundle'
p=json.loads((n/'plan.json').read_text());op=json.loads((original/'plan.json').read_text())
def guard():
 assert sha(original/'plan.json')==e['original_counter_plan_sha256']
 for rel,h in e['code_sha256'].items():assert sha(r/rel)==h,rel
 for rel,h in e['active_counter_inputs_sha256'].items():assert sha(r/rel)==h,rel
 for arm,h in e['source_sha256'].items():assert sha(n/'sources'/arm/'test_counter.c')==h
 assert sha(n/'plan.json')==e['plan_sha256'] and sha(n/'PROTOCOL.md')==e['protocol_sha256']
 for unit,info in e['original_builds'].items():assert sha(original/info['elf_path'])==info['elf_sha256']
assert sha(Path(os.environ['RTC_IMAGE']))==e['image_sha256'];guard()
save(out/'job_metadata/input_before.json',{'passed':True,'active_seals':len(e['active_counter_inputs_sha256']),'execution_sha256':sha(n/'execution.json')})
for name in ['execution.json','execution.sha256','plan.json','PROTOCOL.md','approval.json','COST.json','PREDICTIONS.json']:
 shutil.copyfile(n/name,out/'job_metadata'/name)
for rel,h in op['input_sha256'].items():
 source=original/rel;assert sha(source)==h,rel
 target=b/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for arm,h in e['source_sha256'].items():
 target=b/'apps'/('natural-'+arm);shutil.copytree(b/'apps/V0',target)
 shutil.copyfile(n/'sources'/arm/'test_counter.c',target/'src/test_counter.c');assert sha(target/'src/test_counter.c')==h
shutil.copyfile(n/'plan.json',b/'plan.json');(b/p['output_relative']).mkdir(parents=True)
for arm in e['source_sha256']:
 dest=out/'sources'/arm;dest.mkdir(parents=True);shutil.copyfile(n/'sources'/arm/'test_counter.c',dest/'test_counter.c')
env=dict(os.environ,RTC_NATURAL_BUNDLE=str(b),RTC_NATURAL_OUT_REL=p['output_relative'],RTC_NATURAL_EXECUTION_SHA=sha(n/'execution.json'))
def launch(group,mode,ids,workers):
 folder=out/'launcher'/group;folder.mkdir(parents=True);jf=folder/'jobfile'
 jf.write_text(''.join(shlex.join(['bash',str(n/'task.sh'),mode,str(i)])+'\n' for i in ids))
 le=dict(env,LAUNCHER_PPN=str(workers),LAUNCHER_NHOSTS='1',LAUNCHER_LOCALHOST='1',LAUNCHER_SCHED='interleaved',LAUNCHER_BIND='1',LAUNCHER_WORKDIR=str(folder),LAUNCHER_JOB_FILE=str(jf),LAUNCHER_LOGFILE=str(folder/'launcher.log'))
 for key in ['LAUNCHER_RMI','LAUNCHER_HOSTFILE','LAUNCHER_RMI_HOSTFILE']:le.pop(key,None)
 code=subprocess.run([str(Path(le['LAUNCHER_DIR'])/'paramrun')],env=le,cwd=folder).returncode
 save(folder/'result.json',{'exit_code':code});return code
stage='reuse_builds'
try:
 prior=Path(e['reused_builds_physical_root'])
 for rel,digest in e['reused_build_files_sha256'].items():assert sha(prior/rel)==digest,rel
 for u in p['units']:shutil.copytree(prior/u['id'],out/'builds'/u['id'])
 for rel,digest in e['reused_build_files_sha256'].items():assert sha(out/'builds'/rel)==digest,rel
 for u in p['units']:
  br=json.loads((out/'builds'/u['id']/'build_record.json').read_text());assert br['status']=='built'
 from checks import assess
 stage='nominal';assert launch('nominal','run',[t['index'] for t in p['tasks'] if t['stage']=='nominal'],32)==0
 nominal=assess(out,p,e,['nominal']);save(out/'job_metadata/nominal_gate.json',nominal);assert nominal['qualified']
 stage='primary';launch('primary','run',[t['index'] for t in p['tasks'] if t['stage']=='primary'],32)
 stage='diagnostic_replay';launch('diagnostic_replay','run',[t['index'] for t in p['tasks'] if t['stage']=='diagnostic_replay'],32)
 save(out/'job_metadata/assessment.json',assess(out,p,e,['nominal','primary','diagnostic_replay']))
finally:
 guard();save(out/'job_metadata/input_after.json',{'passed':True,'active_seals':len(e['active_counter_inputs_sha256']),'execution_sha256':sha(n/'execution.json'),'last_stage':stage})
