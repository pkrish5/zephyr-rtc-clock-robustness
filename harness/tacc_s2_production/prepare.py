#!/usr/bin/env python3
"""Prepare primary production only after verified calibration acceptance."""
import argparse,copy,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
COHORT=['f4-rtc','f4-counter','f4-seconds','f767-rtc','f767-counter','f767-seconds','f746-rtc','f746-seconds','h753-rtc','h753-counter','h753-seconds']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
ap=argparse.ArgumentParser();ap.add_argument('--original',type=Path,required=True);ap.add_argument('--accepted-evidence',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();e=a.accepted_evidence
for rel,d in json.loads((e/'files.sha256.json').read_text()).items():assert sha(e/rel)==d,rel
accept=json.loads((e/'raw/acceptance_report.json').read_text());assert accept['all_15_accepted'] is True and accept['production_condition_satisfied'] is True
assert len(accept['settings'])==15 and all(x['accepted'] for x in accept['settings'])
old=json.loads((a.original/'plan.json').read_text());assert sha(a.original/'plan.json')==(a.original/'plan.sha256').read_text().split()[0]
a.out.mkdir(parents=True,exist_ok=False)
for rel,d in old['input_sha256'].items():
    assert sha(a.original/rel)==d,rel
    dst=a.out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.original/rel,dst)
# Package the exact F7 SVD and its index already verified during qualification.
prior=ROOT/'artifacts/s2_qualification_20261025_v1/returned_evidence_20261026/evidence_v1/runtime-cache-blobs'
for digest,dstrel in [('9b806b03ac7078f3ec5a3f39d61cb2b8442605ebd837015ef5539b08c57530dd','renode-cache/cached_binaries/bin1'),('e5891e0c78191c122eca62fe5197d1522a50e653683e738c389d103c7e343a45','renode-cache/binaries_index')]:
    src=prior/digest;assert sha(src)==digest;dst=a.out/dstrel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
p=copy.deepcopy(old);p['phase']='S2 conditionally approved primary production';p['registered_date']='2026-10-26';p['production_authorized']=True
p['output_relative']='results/s2_production_20261026_v1';p['units']=[u for u in old['units'] if u['id'] in COHORT]
assert [u['id'] for u in p['units']]==COHORT
p['boards']={k:v for k,v in old['boards'].items() if k!='f072'}
p['tasks']=[]
for s in range(102):
    for u in p['units']:
        b=p['boards'][u['board_id']]
        freq=b['seeded_frequencies_hz'][s] if s<100 else b['minimum'] if s==100 else b['maximum']
        p['tasks'].append(dict(index=len(p['tasks']),unit_id=u['id'],frequency_hz=freq,
            condition='seeded' if s<100 else 'min' if s==100 else 'max',**({'seed':s} if s<100 else {})))
p['input_sha256']={str(f.relative_to(a.out)):sha(f) for f in a.out.rglob('*') if f.is_file()}
p['design_sha256']=sha(ROOT/'paper/DESIGN.md');p['code_sha256']={**old['code_sha256'],**{str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'harness/tacc_s2_production').glob('*') if f.is_file()}}
p['conditional_approval_evidence']=dict(report_sha256=sha(e/'raw/acceptance_report.json'),report=accept,
    qualification_plan_sha256=sha(a.original/'plan.json'),unchanged_simulation_worker_sha256=old['code_sha256']['harness/tacc_s2/worker.py'])
p['packaging_changes']=dict(f7_svd_pinned=True,source_or_elf_changes=[],outer_partition_adapter='normal, no partition spoofing')
p['build_output_relative']=old['output_relative'];p['maximum_workers']=32;p['node_count']=1;p['walltime']='06:00:00';p['primary_estimated_su']=4.48;p['reservation_su_ceiling']=6
baseline=json.loads((ROOT/'results/s2_qualification_20261025_v1/qualification_report.json').read_text())
wall={u['unit_id']:u['max_wall_seconds'] for u in baseline['units']}
for r in accept['settings']:wall[r['unit_id']]=max(wall[r['unit_id']],r['wall_seconds'])
p['primary_estimated_su']=sum(102*wall[u['id']]/32/3600*1.5 for u in p['units'])
p['costing']='max returned per-app wall across qualification and continuation, 32 workers, 1.5 safety; excludes replay/reference work'
p['activation_gate']='all fifteen calibration settings accepted before preparation; exact accepted report sealed'
save(a.out/'approved_calibration.json',accept)
p['input_sha256']['approved_calibration.json']=sha(a.out/'approved_calibration.json')
save(a.out/'plan.json',p);(a.out/'plan.sha256').write_text(sha(a.out/'plan.json')+'  plan.json\n')
print(json.dumps(dict(plan_sha256=sha(a.out/'plan.json'),configurations=COHORT,launches=len(p['tasks']),estimated_primary_su=p['primary_estimated_su'],reservation_su_ceiling=6)))
