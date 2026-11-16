#!/usr/bin/env python3
import hashlib,json,os,shlex,shutil,subprocess
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
r=Path(os.environ['RTC_REPO']);n=r/'notes/counter_boundary_execution_2026-11-15_v1';ep=n/'execution.json';e=json.loads(ep.read_text())
assert sha(ep)==(n/'execution.sha256').read_text().split()[0]
assert os.environ['SLURM_JOB_PARTITION']=='development' and os.environ['SLURM_JOB_ACCOUNT'].upper()=='CCR26073'
b=r/e['original_bundle_relative'];p=json.loads((b/'plan.json').read_text());out=Path(os.environ['RTC_JOB_OUTPUT'])
assert sha(b/'plan.json')==e['original_counter_plan_sha256']
assert sha(Path(os.environ['RTC_IMAGE']))==e['image_sha256']
def guard():
 for rel,h in e['code_sha256'].items():assert sha(r/rel)==h,rel
 for rel,h in e['active_counter_inputs_sha256'].items():assert sha(r/rel)==h,rel
 for unit,info in e['original_builds'].items():
  assert sha(b/info['elf_path'])==info['elf_sha256'],unit
  assert sha(b/p['output_relative']/'builds'/unit/'build_record.json')==info['build_record_sha256'],unit
 assert sha(n/'PROTOCOL.md')==e['protocol_sha256']
guard()
save(out/'job_metadata/input_before.json',{'passed':True,'active_seals':len(e['active_counter_inputs_sha256']),'execution_sha256':sha(ep)})
for name in ['execution.json','execution.sha256','PROTOCOL.md','approval.json']:
 shutil.copyfile(n/name,out/'job_metadata'/name)
info=e['original_builds']['f4-counter-V0']
for mode in ['off','on']:
 for source in [b/info['elf_path'],b/p['output_relative']/'builds/f4-counter-V0/build_record.json']:
  target=out/mode/source.relative_to(b/p['output_relative']);target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,target);assert sha(source)==sha(target)
folder=out/'launcher';folder.mkdir();jobfile=folder/'jobfile'
jobfile.write_text(''.join(shlex.join(['bash',str(n/'task.sh'),mode])+'\n' for mode in ['off','on']))
env=dict(os.environ,RTC_COUNTER_BUNDLE=str(b),RTC_BOUNDARY_OUT_REL=p['output_relative'],RTC_BOUNDARY_EXECUTION_SHA=sha(ep),LAUNCHER_PPN='2',LAUNCHER_NHOSTS='1',LAUNCHER_LOCALHOST='1',LAUNCHER_SCHED='interleaved',LAUNCHER_BIND='1',LAUNCHER_WORKDIR=str(folder),LAUNCHER_JOB_FILE=str(jobfile),LAUNCHER_LOGFILE=str(folder/'launcher.log'))
for key in ['LAUNCHER_RMI','LAUNCHER_HOSTFILE','LAUNCHER_RMI_HOSTFILE']:env.pop(key,None)
result=subprocess.run([str(Path(env['LAUNCHER_DIR'])/'paramrun')],env=env,cwd=folder)
save(out/'job_metadata/launcher_result.json',{'exit_code':result.returncode})
guard();save(out/'job_metadata/input_after.json',{'passed':True,'active_seals':len(e['active_counter_inputs_sha256']),'execution_sha256':sha(ep)})
# Scientific gate is independently assessed locally, even if the coordinator exits zero.
raise SystemExit(result.returncode)
