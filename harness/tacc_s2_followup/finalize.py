#!/usr/bin/env python3
"""Derive final qualification cohort after independently verifying continuation."""
import argparse,collections,csv,hashlib,json
from pathlib import Path
COHORT=['f4-rtc','f4-counter','f4-seconds','f767-rtc','f767-counter','f767-seconds','f746-rtc','f746-seconds','h753-rtc','h753-counter','h753-seconds']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def verify(e):
    for rel,d in json.loads((e/'files.sha256.json').read_text()).items():assert sha(e/rel)==d,rel
ap=argparse.ArgumentParser();ap.add_argument('--original-evidence',type=Path,required=True);ap.add_argument('--continuation-evidence',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();verify(a.original_evidence);verify(a.continuation_evidence)
old=json.loads((a.original_evidence/'plan.json').read_text());p=json.loads((a.continuation_evidence/'plan.json').read_text());accept=json.loads((a.continuation_evidence/'raw/acceptance_report.json').read_text())
assert accept['all_15_accepted'] and accept['production_condition_satisfied'] and len(accept['settings'])==15
for key in ('units','boards','tasks','upstream_input_sha256','original_platform_sha256','image_sha256','input_sha256','renode_version','step_ns','code_sha256'):
    assert old[key]==p[key],key
rows={};origin={}
for label,e in [('original',a.original_evidence),('continuation',a.continuation_evidence)]:
    for f in (e/'raw/records').glob('*.json'):
        r=json.loads(f.read_text());assert r['index'] not in rows
        rows[r['index']]=r;origin[r['index']]=dict(attempt=label,record_sha256=sha(f))
units=[];cases=[];boards=collections.defaultdict(lambda:dict(applications=0,declared=0,runnable=0,capability_skipped=0,expected_launches=0,case_verdict_slots=0))
for uid in COHORT:
    u=next(u for u in old['units'] if u['id']==uid);ts=[t for t in old['tasks'] if t['unit_id']==uid]
    rs=[rows[t['index']] for t in ts];assert len(rs)==12
    assert all(r['application_completed'] and r['outcome']=='complete' and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'] for r in rs)
    ns=[r for r in rs if r['condition']=='nominal'];assert len(ns)==5
    ds={d for r in rs for d in r['rtc_divider_observations'] if d>1};assert ds=={32000},uid
    nrun=nskip=0
    for case in u['expected_declared_cases']:
        st=[next(c['status'] for c in r['cases'] if c['case']==case) for r in ns]
        assert len(set(st))==1 and st[0] in ('pass','skip'),(uid,case,st)
        nrun+=st[0]=='pass';nskip+=st[0]=='skip'
        cases.append(dict(unit_id=uid,case=case,nominal_status=st[0],nominal_launches=5,calibration_launches=7,production_retained=True))
    units.append(dict(board=old['boards'][u['board_id']]['board'],unit_id=uid,declared_cases=len(u['expected_declared_cases']),runnable_nominal_cases=nrun,capability_skipped_nominal_cases=nskip,nominal_launches=5,calibration_launches=7,expected_production_launches=102,expected_case_verdict_slots=102*len(u['expected_declared_cases']),maximum_wall_seconds=max(r['wall_seconds'] for r in rs)))
    b=boards[u['board_id']];b['applications']+=1;b['declared']+=len(u['expected_declared_cases']);b['runnable']+=nrun;b['capability_skipped']+=nskip;b['expected_launches']+=102;b['case_verdict_slots']+=102*len(u['expected_declared_cases'])
a.out.mkdir(parents=True,exist_ok=False)
for name,data in [('cohort.csv',units),('per_case_cohort.csv',cases)]:
    with (a.out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
save(a.out/'report.json',dict(configurations=units,boards=dict(boards),production_condition_satisfied=True,
    declared_case_slots_per_setting=sum(u['declared_cases'] for u in units),expected_launches=sum(u['expected_production_launches'] for u in units),expected_case_verdict_slots=sum(u['expected_case_verdict_slots'] for u in units),
    primary_estimated_su=sum(102*u['maximum_wall_seconds']/32/3600*1.5 for u in units),
    costing='maximum observed per-application wall, 32 workers, 1.5 allowance; primary-only',
    original_missing_outcomes_preserved=True,record_origins=origin,board_replicas_are_not_independent=True,
    original_plan_sha256=sha(a.original_evidence/'plan.json'),continuation_plan_sha256=sha(a.continuation_evidence/'plan.json')))
print(json.dumps(dict(boards=dict(boards),configurations=len(units),expected_launches=1122)))
