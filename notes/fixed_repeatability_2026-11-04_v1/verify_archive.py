#!/usr/bin/env python3
"""Verify packed repeatability evidence, retaining complete/interrupted/failed states."""
import argparse,gzip,hashlib,importlib.util,json,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--returned',type=Path,required=True);p.add_argument('--job',required=True);p.add_argument('--unit',choices=['f4-rtc','f4-counter'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
stem=f'{a.job}-fixed-repeat-{a.unit}';receipt=json.loads((a.returned/(stem+'.json')).read_text());archive=a.returned/(stem+'.tar.gz');mp=a.returned/(stem+'.manifest.json.gz')
assert receipt['slurm_job_id']==a.job and receipt['output_state'] in ['complete','interrupted','failed']
assert sha(archive)==receipt['archive_sha256']==(a.returned/(stem+'.tar.gz.sha256')).read_text().split()[0]
assert sha(mp)==receipt['manifest_sha256']
manifest=json.loads(gzip.decompress(mp.read_bytes()))['files'];assert len(manifest)==receipt['archive_entries']
spec=importlib.util.spec_from_file_location('archive_helper',ROOT/'harness/tacc_storage/archive.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.verify(archive,manifest)
a.out.mkdir(exist_ok=False,parents=True)
with tarfile.open(archive) as tar:
 for item in tar:
  rel=PurePosixPath(item.name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0]=='output';dest=a.out/item.name
  if item.isdir():dest.mkdir(exist_ok=True,parents=True)
  else:
   assert item.isfile();dest.parent.mkdir(exist_ok=True,parents=True)
   with tar.extractfile(item) as src,dest.open('xb') as dst:
    import shutil;shutil.copyfileobj(src,dst)
out=a.out/'output';assert m.inventory(out)==manifest
for stage in ['before','after']:
 d=json.loads((out/f'job_metadata/protected_{stage}.json').read_text());assert d['count']==30067 and not d['changed']
 original=json.loads((ROOT/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json').read_text())['hashes']
 assert set(d['files'])==set(original) and all(v['before_sha256']==v['after_sha256']==original[k] for k,v in d['files'].items())
plan=ROOT/'notes/fixed_repeatability_2026-11-04_v1/packet/plan.json'
if (out/'job_metadata/plan.json').exists():assert sha(out/'job_metadata/plan.json')==sha(plan)
proof=dict(job_id=a.job,unit=a.unit,archive_sha256=sha(archive),exact_entries=len(manifest),output_state=receipt['output_state'],protected_files_unchanged=30067)
(a.out/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
