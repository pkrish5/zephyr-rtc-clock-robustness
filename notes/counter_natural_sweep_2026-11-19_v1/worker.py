#!/usr/bin/env python3
import hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
N=Path('/repo/notes/counter_natural_sweep_2026-11-19_v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((N/'execution.json').read_text());assert sha(N/'execution.json')==os.environ['RTC_NATURAL_EXECUTION_SHA']
assert os.environ['SLURM_JOB_PARTITION']=='normal' and os.environ['SLURM_JOB_ACCOUNT'].upper()=='CCR26073'
for rel,h in e['code_sha256'].items():assert sha(Path('/repo')/rel)==h,rel
b=Path('/bundle');assert sha(b/'plan.json')==e['plan_sha256'];p=json.loads((b/'plan.json').read_text())
for rel,h in p['input_sha256'].items():assert sha(b/rel)==h,rel
for arm,h in e['source_sha256'].items():assert sha(b/'apps'/('natural-'+arm)/'src/test_counter.c')==h
spec=importlib.util.spec_from_file_location('frozen','/repo/harness/tacc_s2/worker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=m.provenance;m.provenance=lambda bundle:dict(base(bundle),natural_execution_sha256=sha(N/'execution.json'),phase_control=False,observer=False)
mode,index=sys.argv[1],int(sys.argv[2])
if mode=='build':
 u=p['units'][index];m.build(b,p,u);folder=b/p['output_relative']/'builds'/u['id'];br=json.loads((folder/'build_record.json').read_text());assert br['status']=='built'
 intermediate=Path('/scratch-builds')/u['id'];assert not intermediate.exists();shutil.move(str(folder/'build'),intermediate)
 for rel in ['zephyr/zephyr.elf',*br['build_products_sha256']]:
  target=folder/'build'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(intermediate/rel,target)
else:
 assert mode=='run';t=p['tasks'][index]
 if t['stage']=='nominal':
  p=dict(p,units=[dict(u,wall_timeout_seconds=3600,max_virtual_seconds=450) for u in p['units']])
 m.run(b,p,t)
