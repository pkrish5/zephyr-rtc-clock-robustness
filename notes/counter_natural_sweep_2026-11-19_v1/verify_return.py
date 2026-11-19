#!/usr/bin/env python3
"""Independent archive verification, preserving failed/interrupted publication states."""
import argparse,gzip,hashlib,importlib.util,json,tarfile
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--returned',type=Path,required=True);ap.add_argument('--job',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--sacct-json',type=Path,required=True);a=ap.parse_args()
 root=Path(__file__).resolve().parents[2];note=Path(__file__).resolve().parent
 stem=a.job+'-natural-sweep';receipt=json.loads((a.returned/(stem+'.json')).read_text());archive=a.returned/(stem+'.tar.gz');manifest=a.returned/(stem+'.manifest.json.gz')
 assert receipt['slurm_job_id']==a.job and receipt['account'].upper()=='CCR26073' and receipt['partition']=='normal'
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
 for name in ['execution.json','execution.sha256','PROTOCOL.md','approval.json','plan.json','COST.json','PREDICTIONS.json']:
  p=out/'job_metadata'/name
  if p.exists():assert sha(p)==sha(note/name),name
 e=json.loads((note/'execution.json').read_text());assert receipt['container_sha256']==e['image_sha256']
 result={'job_id':a.job,'output_state':receipt['output_state'],'archive_sha256':sha(archive),'archive_entries':len(files),'exact_inventory':True,'protection_complete':all(protection.values()),'protected_stages':protection,'scientific_gate_evaluated':False}
 (a.out/'archive_verification.json').write_text(json.dumps(result,indent=2)+'\n')
 state=json.loads(a.sacct_json.read_text());assert str(state['job_id'])==a.job
 p=json.loads((note/'plan.json').read_text())
 integrity=[]
 for side in ('before','after'):
  f=out/'job_metadata'/('input_'+side+'.json');d=json.loads(f.read_text()) if f.exists() else {}
  integrity.append(d.get('passed') is True and d.get('active_seals')==764 and d.get('execution_sha256')==sha(note/'execution.json'))
 for arm,digest in e['source_sha256'].items():assert sha(out/'sources'/arm/'test_counter.c')==digest
 from checks import assess
 report=assess(out,p,e,['nominal','primary','diagnostic_replay'])
 report.update(archive=result,sacct=state,input_guards=all(integrity),job_id=a.job)
 report['verified_complete']=result['protection_complete'] and all(integrity) and report['qualified'] and len(report['rows'])==140 and all(r.get('integrity') and r.get('complete') for r in report['rows']) and state['state']=='COMPLETED' and state['exit_code']=='0:0'
 (a.out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'job_id':a.job,'archive':result,'nominal_qualified':report['qualified'],'verified_complete':report['verified_complete'],'records':len(report['rows'])},indent=2))
if __name__=='__main__':main()
