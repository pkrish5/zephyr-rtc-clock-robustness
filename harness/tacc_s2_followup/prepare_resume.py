#!/usr/bin/env python3
"""Seal the exact user-approved calibration continuation, without execution."""
import argparse, copy, csv, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INDICES=[18,19,21,55,56,58,71,72,79,119,120,127,140,141,143]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')

ap=argparse.ArgumentParser();ap.add_argument('--original',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();old=json.loads((a.original/'plan.json').read_text());assert sha(a.original/'plan.json')==(a.original/'plan.sha256').read_text().split()[0]
a.out.mkdir(parents=True,exist_ok=False)
for rel,d in old['input_sha256'].items():
    assert sha(a.original/rel)==d,rel
    dst=a.out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.original/rel,dst)
new=copy.deepcopy(old)
new['design_sha256']=sha(ROOT/'paper/DESIGN.md')
new['verified_f7_svd_sha256']='9b806b03ac7078f3ec5a3f39d61cb2b8442605ebd837015ef5539b08c57530dd'
new['acceptance']={}
base=ROOT/'artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/raw/records'
for i in INDICES:
    t=old['tasks'][i]
    n=next(n for n in old['tasks'] if n['unit_id']==t['unit_id'] and n['condition']=='nominal')
    r=json.loads((base/f"{n['unit_id']}-nominal-{n['index']:03d}.json").read_text())
    vector={c['case']:c['status'] for c in r['cases']}
    expected=dict(vector)
    if i in (71,72):expected['seconds_counter.test_seconds_rate']='fail'
    new['acceptance'][str(i)]=dict(nominal_vector=vector,expected_vector=expected)
new['continuation']=dict(date='2026-10-26',original_plan_sha256=sha(a.original/'plan.json'),
 task_indices=INDICES,original_missing_outcomes_preserved=True,
 purpose='Finish exactly fifteen interrupted/unstarted calibration settings; no source/config/runtime change')
new['followup_code_sha256']={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'harness/tacc_s2_followup').glob('*') if p.is_file()}
for rel,d in new['code_sha256'].items():assert sha(ROOT/rel)==d,rel
for key in ('units','boards','tasks','upstream_input_sha256','original_platform_sha256','image_sha256','input_sha256','renode_version','step_ns'):
    assert old[key]==new[key],key
save(a.out/'plan.json',new);(a.out/'plan.sha256').write_text(sha(a.out/'plan.json')+'  plan.json\n')
print(json.dumps(dict(plan_sha256=sha(a.out/'plan.json'),indices=INDICES,changed_scientific_inputs=[])))
