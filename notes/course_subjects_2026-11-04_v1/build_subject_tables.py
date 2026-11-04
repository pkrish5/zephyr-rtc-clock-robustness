#!/usr/bin/env python3
"""Readable manuscript views of existing reconciled records; no experiments.
Run `make tables EVIDENCE_ARCHIVE=...` first, then this script.
The eight pinned tables stay unchanged and remain the detailed artifact tables.
"""
import csv, hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
P=ROOT/'notes/final_submission_2026-11-02_v1/phase3_package_v2'
OUT=ROOT/'paper/draft/tables'
def read(name):
    with (P/name).open(newline='') as f: return list(csv.DictReader(f))
rows=read('repair_primary_index.csv')
assert len(rows)==17375
variants=['V0','V1','V1b','V2','V3']
subject=lambda r:r['version_id'].rsplit('--',1)[0]
ids=[('human-rtc_alarm_callback','Alarm callback'),('human-rtc_alarm_pending','Alarm pending'),('human-rtc_time_counting','Calendar counting'),('sol-range_absent-rtc_alarm_pending-r01','Sol pending r01'),('sol-range_absent-rtc_alarm_pending-r03','Sol pending r03'),('astra-range_absent-rtc_alarm_pending-r05','Astra pending r05')]
lines=[r'\begin{tabular}{@{}lrrrrrrl@{}}\toprule',r'& \multicolumn{2}{c}{V0 failures} & \multicolumn{4}{c}{Legal passes / 102 settings} & Slow fault\\',r'Subject & Seeds / 100 & Ends / 2 & V1 & V1b & V2 & V3 & V0 $\to$ each repair\\\midrule']
ledger=[]
for i,(sid,label) in enumerate(ids):
    if i in (0,3): lines.append(r'\multicolumn{8}{@{}l}{\emph{'+('Upstream, isolated cases' if i==0 else 'Generated, base prompt')+r'}}\\')
    rr=[r for r in rows if subject(r)==sid]
    f=[]
    for c in ['seeded','min','max']:
        f.append(sum(r['variant']=='V0' and r['operator']=='legal' and r['condition']==c and r['outcome']=='fail' for r in rr))
    passes=[]
    for v in variants:
        legal=[r for r in rr if r['variant']==v and r['operator']=='legal']
        assert len(legal)==102 and all(r['outcome'] in ('pass','fail') for r in legal)
        slow=[r for r in rr if r['variant']==v and r['operator']=='slow']
        assert len(slow)==1 and slow[0]['evaluable']=='True' and slow[0]['detected']=='True'
        if v!='V0':
            assert all(r['outcome']=='pass' for r in legal)
            passes.append('102/102')
    lines.append(label+' & '+str(f[0])+'/100 & '+str(sum(f[1:]))+'/2 & '+' & '.join(passes)+r' & detect $\to$ detect\\')
    ledger.append(dict(subject_id=sid,label=label,original_seed_fail=f[0],original_endpoint_fail=sum(f[1:]),repaired_pass_per_variant=102,missing_per_variant=0,slow_all_variants='detected'))
lines.append(r'\bottomrule\end{tabular}')
(OUT/'subjects_course_v2.tex').write_text('\n'.join(lines)+'\n')
lines=[r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'Variant & Seed F/M & Slow & Early & Late & Median (s)\\\midrule']
for r in read('repair_per_variant.csv'):
    # Column names are verified below, never inferred from expected prose.
    v=r['variant']
    rr=[x for x in rows if x['variant']==v]
    legal=[x for x in rr if x['operator']=='legal' and x['condition']=='seeded']
    counts=Counter(x['outcome'] for x in legal)
    cell=[]
    for op in ['slow','offset_early','offset_late']:
        op_rows=[x for x in rr if x['operator']==op and x['evaluable']=='True']
        cell.append(str(sum(x['detected']=='True' for x in op_rows))+'/'+str(len(op_rows)))
    from statistics import median
    med=median(float(x['virtual_seconds']) for x in legal if x['outcome'] in ('pass','fail'))
    lines.append(f"{v} & {counts['fail']}/{counts['harness_error']} & "+' & '.join(cell)+f' & {med:.1f}'+r'\\')
lines.append(r'\bottomrule\end{tabular}')
(OUT/'repairs_course_v2.tex').write_text('\n'.join(lines)+'\n')
# Clear expansion labels, retaining replicas and failures attributed elsewhere.
by={}
for r in read('s2_per_case_with_references.csv'):
    b=by.setdefault(r['board_id'],dict(run=set(),skip=set(),wait=set(),cascade=set(),rate=set()))
    if int(r['pass_count'])+int(r['fail_count']): b['run'].add(r['case'])
    else: b['skip'].add(r['case'])
    if int(r['fail_count']): b[{'a':'wait','b':'wait','c':'cascade','d':'rate'}[r['category']]].add(r['case'])
lines=[r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'Configuration & Run & Skip & Wait & Cascade & Rate\\\midrule']
for key,label in [('f4','F4'),('f767','F767 (F4 replica)'),('f746','F746'),('h753','H753')]:
    b=by[key]
    lines.append(label+' & '+' & '.join(str(len(b[k])) for k in ['run','skip','wait','cascade','rate'])+r'\\')
lines.append(r'\bottomrule\end{tabular}')
(OUT/'expanded_course_v2.tex').write_text('\n'.join(lines)+'\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*_course_v2.tex')}
(HERE/'subject_table_audit.json').write_text(json.dumps(dict(subjects=ledger,table_sha256=manifest,source_sha256=hashlib.sha256((P/'repair_primary_index.csv').read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(manifest,indent=2))
