#!/usr/bin/env python3
import hashlib, importlib.util, json, os, sys
from pathlib import Path
N=Path('/repo/notes/counter_boundary_execution_2026-11-15_v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((N/'execution.json').read_text())
assert sha(N/'execution.json')==os.environ['RTC_BOUNDARY_EXECUTION_SHA']
for rel,h in e['code_sha256'].items():assert sha(Path('/repo')/rel)==h,rel
assert os.environ['SLURM_JOB_PARTITION']=='development'
assert os.environ['SLURM_JOB_ACCOUNT'].upper()=='CCR26073'
mode=sys.argv[1];assert mode in ('off','on')
b=Path('/bundle');p=json.loads((b/'plan.json').read_text())
assert sha(b/'plan.json')==e['original_counter_plan_sha256']
for rel,h in p['input_sha256'].items():assert sha(b/rel)==h,rel
for rel,h in p['code_sha256'].items():assert sha(Path('/repo')/rel)==h,rel
elf=b/e['original_builds']['f4-counter-V0']['elf_path']
assert sha(elf)==e['original_builds']['f4-counter-V0']['elf_sha256']
sys.path.insert(0,'/opt/rtc-code/harness/phase0')
import session
original=session.RenodeSession
class Observed(original):
 def __enter__(self):
  super().__enter__()
  if mode=='on':
   for label,address in e['hooks'].items():
    script="print 'BOUNDARY_OBS|%s|%%s|%%s' %% (machine.ElapsedVirtualTime.TimeElapsed.TotalNanoseconds, machine.SystemBus.ReadDoubleWord(0x40002828))"%label
    self.command('cpu AddHook 0x%x "%s"'%(address,script))
  return self
session.RenodeSession=Observed
spec=importlib.util.spec_from_file_location('s2', '/repo/harness/tacc_s2/worker.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
task=next(t for t in p['tasks'] if t['unit_id']=='f4-counter-V0' and t['stage']=='gate' and t['frequency_hz']==32000)
m.run(b,p,task)
