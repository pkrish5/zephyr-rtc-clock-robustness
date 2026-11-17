#!/usr/bin/env python3
"""Independent archive verification, preserving failed/interrupted publication states."""
import argparse,gzip,hashlib,importlib.util,json,tarfile
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--returned',type=Path,required=True);ap.add_argument('--job',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--sacct-json',type=Path,required=True);a=ap.parse_args()
 root=Path(__file__).resolve().parents[2];note=Path(__file__).resolve().parent
 stem=a.job+'-phase-qualification';receipt=json.loads((a.returned/(stem+'.json')).read_text());archive=a.returned/(stem+'.tar.gz');manifest=a.returned/(stem+'.manifest.json.gz')
 assert receipt['slurm_job_id']==a.job and receipt['account'].upper()=='CCR26073' and receipt['partition']=='development'
 assert sha(archive)==receipt['archive_sha256']==(a.returned/(stem+'.tar.gz.sha256')).read_text().split()[0]
 assert sha(manifest)==receipt['manifest_sha256']
 files=json.loads(gzip.decompress(manifest.read_bytes()))['files'];assert len(files)==receipt['archive_entries']
 assert all(x['kind'] in ('file','directory') for x in files.values())
 spec=importlib.util.spec_from_file_location('archive_helper',root/'harness/tacc_storage/archive.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 helper.verify(archive,files)
 a.out.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive) as tar:
  for m in tar:
   target=a.out/m.name
   assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
   if m.isdir():target.mkdir(parents=True,exist_ok=True)
   else:
    assert m.isfile();target.parent.mkdir(parents=True,exist_ok=True)
    with tar.extractfile(m) as src,target.open('xb') as dst:
     while block:=src.read(1048576):dst.write(block)
 out=a.out/'output';assert helper.inventory(out)==files
 baseline=json.loads((root/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json').read_text())['hashes']
 protection={}
 for side in ('before','after'):
  p=out/f'job_metadata/protected_{side}.json'
  if not p.exists():protection[side]=False;continue
  d=json.loads(p.read_text());assert d['count']==len(baseline)==30067 and not d['changed']
  assert set(d['files'])==set(baseline)
  assert all(v['before_sha256']==v['after_sha256']==baseline[k] for k,v in d['files'].items())
  protection[side]=True
 for name in ['execution.json','execution.sha256','PROTOCOL.md','approval.json','plan.json','COST.json']:
  p=out/'job_metadata'/name
  if p.exists():assert sha(p)==sha(note/name),name
 e=json.loads((note/'execution.json').read_text());assert receipt['container_sha256']==e['image_sha256']
 result={'job_id':a.job,'output_state':receipt['output_state'],'archive_sha256':sha(archive),'archive_entries':len(files),'exact_inventory':True,'protection_complete':all(protection.values()),'protected_stages':protection,'scientific_gate_evaluated':False}
 (a.out/'archive_verification.json').write_text(json.dumps(result,indent=2)+'\n')
 state=json.loads(a.sacct_json.read_text());assert str(state['job_id'])==a.job
 p=json.loads((note/'plan.json').read_text())
 integrity=[]
 for side in ('before','after'):
  guard=out/'job_metadata'/('input_'+side+'.json')
  d=json.loads(guard.read_text()) if guard.exists() else {}
  integrity.append(d.get('passed') is True and d.get('active_seals')==764 and d.get('execution_sha256')==sha(note/'execution.json'))
 for u in p['units']:
  arm=u['variant'];folder=out/'builds'/u['id']
  if not (folder/'build_record.json').exists():integrity.append(False);continue
  br=json.loads((folder/'build_record.json').read_text());hp=folder/'hooks.json'
  if not hp.exists():integrity.append(False);continue
  h=json.loads(hp.read_text())
  assert sha(out/'sources'/arm/'test_counter.c')==e['source_sha256'][arm]
  assert br['status']=='built' and br['exit_code']==0
  assert sha(folder/'build/zephyr/zephyr.elf')==br['elf_sha256']==h['elf_sha256']
  assert sha(folder/'build.log')==br['log_sha256']
  for rel,digest in br['build_products_sha256'].items():assert sha(folder/'build'/rel)==digest
  assert sha(folder/'alarm_read_disassembly.txt')==h['disassembly_sha256']
  assert br['source_commit']==p['zephyr_commit'] and br['plan_sha256']==e['plan_sha256']
  assert br['config_sha256']==p['input_sha256'][u['config']] and br['overlay_sha256']==p['input_sha256'][u['overlay']]
  for symbol in ('boundary_configuration_magic','boundary_phase_hundredths'):
   x=h['symbols'][symbol];assert x['section_type']==8 and 'noinit' in x['section'] and x['size']==4
  process=out/'processes/build'/str(p['units'].index(u))
  assert json.loads(process.with_suffix('.json').read_text())['exit_code']==0
  integrity.append(True)
 from checks import assess
 gate=assess(out,p,e,['nominal','timing'])
 gate.update(job_id=a.job,sacct=state,archive=result,build_and_guard_integrity=all(integrity))
 gate['passed']=gate['passed'] and all(integrity) and result['protection_complete'] and receipt['output_state']=='complete' and state['state']=='COMPLETED' and state['exit_code']=='0:0'
 (a.out/'qualification.json').write_text(json.dumps(gate,indent=2)+'\n')
 print(json.dumps({'job_id':a.job,'passed':gate['passed'],'records':len(gate['rows']),'qualified_records':sum(x['passed'] for x in gate['rows']),'archive':result},indent=2))
if __name__=='__main__':main()
