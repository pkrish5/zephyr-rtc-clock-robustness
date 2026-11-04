#!/usr/bin/env python3
"""Compute-only seals, packed Launcher run, complete append-only accounting."""
import hashlib,json,os,shlex,subprocess
from collections import Counter
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
def main():
 assert os.environ['SLURM_JOB_PARTITION']=='development'
 repo=Path(os.environ['RTC_REPO']);packet=Path(os.environ['RTC_REPEAT_PACKET']);primary=Path(os.environ['RTC_REPEAT_PRIMARY']);out=Path(os.environ['RTC_JOB_OUTPUT'])
 n=json.loads((packet/'plan.json').read_text());assert sha(packet/'plan.json')==(packet/'plan.sha256').read_text().split()[0]
 assert sha(Path(os.environ['RTC_IMAGE']))==n['image_sha256']
 assert sha(primary/'plan.json')==n['base_plan_sha256']
 p=json.loads((primary/'plan.json').read_text())
 for rel,h in p['input_sha256'].items():assert sha(primary/rel)==h,rel
 for rel,h in n['code_sha256'].items():assert sha(repo/rel)==h,rel
 for rel,h in n['counter_inputs_sha256'].items():assert sha(repo/rel)==h,rel
 assert sha(packet/'PROTOCOL.md')==n['protocol_sha256']
 for unit,info in n['unit_builds'].items():
  assert sha(primary/info['elf_path'])==info['elf_sha256']
  assert sha(primary/p['output_relative']/'builds'/unit/'build_record.json')==info['build_record_sha256']
 save(out/'job_metadata/input_verification_before.json',dict(all_passed=True,repeat_plan_sha256=sha(packet/'plan.json'),counter_inputs_unchanged=True))
 for name in ['plan.json','plan.sha256','PROTOCOL.md','PROTOCOL.sha256','COST.json','input_verification.json']:
  dst=out/'job_metadata'/name;dst.write_bytes((packet/name).read_bytes())
 selected=[t for t in n['tasks'] if t['unit_id']==os.environ['RTC_REPEAT_UNIT']];assert len(selected)==90
 jobfile=out/'launcher/jobfile';jobfile.parent.mkdir()
 with jobfile.open('x') as f:
  for t in selected:f.write(shlex.join(['bash','-l',str(repo/'harness/tacc_fixed_repeatability/task.sh'),str(t['index'])])+'\n')
 env=dict(os.environ,LAUNCHER_PPN='32',LAUNCHER_NHOSTS='1',LAUNCHER_LOCALHOST='1',LAUNCHER_SCHED='interleaved',LAUNCHER_BIND='1',LAUNCHER_WORKDIR=str(jobfile.parent),LAUNCHER_JOB_FILE=str(jobfile),LAUNCHER_LOGFILE=str(jobfile.parent/'launcher.log'))
 for k in ['LAUNCHER_RMI','LAUNCHER_HOSTFILE','LAUNCHER_RMI_HOSTFILE']:env.pop(k,None)
 code=subprocess.run([str(Path(os.environ['LAUNCHER_DIR'])/'paramrun')],cwd=jobfile.parent,env=env).returncode
 summary=[]
 for t in selected:
  rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}";rp=out/'records'/(rid+'.json');status='missing';reason='no primary record'
  if rp.exists():
   r=json.loads(rp.read_text());cases=[c for c in r['cases'] if c['case']==t['selected_case']]
   if r['outcome']=='complete' and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'] and len(cases)==1:
    status=cases[0]['status'];reason='explicit selected-case verdict in complete application'
   else:reason=r.get('error') or 'incomplete/ambiguous application'
  summary.append(dict(**t,selected_outcome=status,reason=reason,primary_record_sha256=sha(rp) if rp.exists() else None))
 for rel,h in n['counter_inputs_sha256'].items():assert sha(repo/rel)==h,rel
 for unit,info in n['unit_builds'].items():assert sha(primary/info['elf_path'])==info['elf_sha256']
 save(out/'job_metadata/input_verification_after.json',dict(all_passed=True,counter_inputs_unchanged=True,original_elf_hashes_unchanged=True))
 save(out/'repeat_summary.json',dict(launcher_exit_code=code,scheduled=len(selected),counts=dict(Counter(r['selected_outcome'] for r in summary)),rows=summary))
 # A finalized missing outcome remains missing, even if its process timed out.
 # Report the process code; never retry, replace, or drop a planned index.
 print(json.dumps(dict(launcher_exit_code=code,counts=dict(Counter(r['selected_outcome'] for r in summary)))))
if __name__=='__main__':main()
