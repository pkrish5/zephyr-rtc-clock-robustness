#!/usr/bin/env python3
"""Qualification adapter; no original worker/source/ELF is modified."""
import hashlib,importlib.util,json,os,re,struct,subprocess,sys,shutil
from pathlib import Path
N=Path('/repo/notes/counter_phase_qualification_2026-11-17_v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
def symbols(elf):
 data=elf.read_bytes();assert data[:6]==b'\x7fELF\x01\x01'
 h=struct.unpack_from('<16sHHIIIIIHHHHHH',data);shoff,shsize,shcount,shnames=h[6],h[11],h[12],h[13]
 sections=[struct.unpack_from('<IIIIIIIIII',data,shoff+i*shsize) for i in range(shcount)]
 names=sections[shnames];strings=data[names[4]:names[4]+names[5]]
 cstr=lambda blob,o:blob[o:blob.index(b'\0',o)].decode()
 result={}
 for sec in sections:
  if sec[1]!=2:continue
  st=sections[sec[6]];stab=data[st[4]:st[4]+st[5]]
  for offset in range(sec[4],sec[4]+sec[5],sec[9]):
   name,val,size,info,other,idx=struct.unpack_from('<IIIBBH',data,offset)
   if name and idx<len(sections):result[cstr(stab,name)]={'address':val&~1 if info&15==2 else val,'size':size,'section':cstr(strings,sections[idx][0]),'section_type':sections[idx][1]}
 return result
mode,index=sys.argv[1],int(sys.argv[2]);b=Path('/bundle');ep=N/'execution.json';e=json.loads(ep.read_text())
assert sha(ep)==os.environ['RTC_PHASE_EXECUTION_SHA']
assert os.environ['SLURM_JOB_PARTITION']=='development' and os.environ['SLURM_JOB_ACCOUNT'].upper()=='CCR26073'
for rel,h in e['code_sha256'].items():assert sha(Path('/repo')/rel)==h,rel
assert sha(b/'plan.json')==e['plan_sha256'];p=json.loads((b/'plan.json').read_text())
for rel,h in p['input_sha256'].items():assert sha(b/rel)==h,rel
for arm,h in e['source_sha256'].items():assert sha(b/'apps'/('phase-'+arm)/'src/test_counter.c')==h,arm
spec=importlib.util.spec_from_file_location('frozen', '/repo/harness/tacc_s2/worker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
if mode=='build':
 u=p['units'][index];m.build(b,p,u)
 folder=b/p['output_relative']/'builds'/u['id'];br=json.loads((folder/'build_record.json').read_text());assert br['status']=='built'
 elf=b/br['elf_path'];sy=symbols(elf)
 required=['boundary_phase_hundredths','boundary_configuration_magic','test_all_channels_instance','rtc_stm32_set_alarm','rtc_stm32_read','alarm_handler2']
 assert all(k in sy for k in required)
 for k in required[:2]:assert sy[k]['section_type']==8 and 'noinit' in sy[k]['section'] and sy[k]['size']==4,(k,sy[k])
 candidates=list(Path('/opt/zephyr-sdk-0.17.4').glob('**/arm-zephyr-eabi-objdump'));assert len(candidates)==1
 lo=sy['rtc_stm32_set_alarm']['address'];hi=lo+sy['rtc_stm32_set_alarm']['size'];assert hi>lo
 dis=subprocess.check_output([str(candidates[0]),'-d',f'--start-address={lo}',f'--stop-address={hi}',str(elf)],text=True)
 calls=re.findall(r'^\s*([0-9a-f]+):\s+[0-9a-f ]+\s+bl\s+[0-9a-f]+\s+<rtc_stm32_read>',dis,re.M);assert calls,'Cannot locate exact scheduling read'
 before=int(calls[0],16);hooks={'case_entry':sy['test_all_channels_instance']['address'],'read_before':before,'read_after':before+4,'callback':sy['alarm_handler2']['address']}
 (folder/'alarm_read_disassembly.txt').write_text(dis)
 save(folder/'hooks.json',{'elf_sha256':sha(elf),'symbols':{k:sy[k] for k in required},'hooks':hooks,'disassembly_sha256':sha(folder/'alarm_read_disassembly.txt'),'first_scheduling_call':True})
 # Move only new intermediate builds outside the packed output; preserve them.
 intermediate=Path('/scratch-builds')/u['id'];assert not intermediate.exists()
 shutil.move(str(folder/'build'),intermediate)
 for rel in ['zephyr/zephyr.elf',*br['build_products_sha256']]:
  source=intermediate/rel;target=folder/'build'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
else:
 assert mode=='run';t=p['tasks'][index];u=next(x for x in p['units'] if x['id']==t['unit_id']);folder=b/p['output_relative']/'builds'/u['id']
 hm=json.loads((folder/'hooks.json').read_text());br=json.loads((folder/'build_record.json').read_text());assert hm['elf_sha256']==br['elf_sha256']==sha(b/br['elf_path'])
 sys.path.insert(0,'/opt/rtc-code/harness/phase0');import session
 base=session.RenodeSession
 class PhaseSession(base):
  def __enter__(self):
   super().__enter__()
   for key,value in [('boundary_phase_hundredths',t['phase_hundredths']),('boundary_configuration_magic',0x42504831)]:
    self.command('sysbus WriteDoubleWord 0x%x 0x%x'%(hm['symbols'][key]['address'],value))
    assert self.read_word(hm['symbols'][key]['address'])==value
   if t['observer']=='on':
    for label,address in hm['hooks'].items():
     script="print 'BOUNDARY_OBS|%s|%%s|%%s' %% (machine.ElapsedVirtualTime.TimeElapsed.TotalNanoseconds, machine.SystemBus.ReadDoubleWord(0x40002828))"%label
     self.command('cpu AddHook 0x%x "%s"'%(address,script))
   return self
 session.RenodeSession=PhaseSession
 original_provenance=m.provenance
 m.provenance=lambda bundle:dict(original_provenance(bundle),phase_execution_sha256=sha(ep),hooks_sha256=sha(folder/'hooks.json'),completion_scope='full_application' if t['stage']=='nominal' else 'selected_case_timing_diagnostic_only')
 if t['stage']=='timing':
  # Stop only this diagnostic at the selected case's explicit result. Never call
  # the unfinished downstream application complete or substitute this for primary data.
  m.CASE=re.compile(r'\b(PASS|FAIL|SKIP) - (test_all_channels) in [0-9.]+ seconds')
  m.MARKERS=(' PASS - test_all_channels in ',' FAIL - test_all_channels in ',' SKIP - test_all_channels in ')
  old_save=m.save
  def diagnostic_save(path,data):
   if 'application_completed' in data:
    data=dict(data,selected_diagnostic_completed=data['application_completed'],application_completed=False,downstream_not_evaluated=True)
   old_save(path,data)
  m.save=diagnostic_save
 m.run(b,p,t)
