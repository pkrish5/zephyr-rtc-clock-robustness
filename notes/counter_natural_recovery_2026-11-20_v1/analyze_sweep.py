#!/usr/bin/env python3
"""Offline primary-only sweep summary; reads independently verified records."""
import argparse,csv,json
from pathlib import Path
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--verified',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=json.loads((a.verified/'assessment.json').read_text());assert d['verified_complete'] and d['qualified'];assert len(d['rows'])==140 and all(r['integrity'] and r['complete'] for r in d['rows']);assert all(x['agreement'] for x in d['replay_comparisons'])
a.out.mkdir(parents=True,exist_ok=False);arms=[('original',3),('deadline_6',6),('derived_fixed',7.648),('derived_poll',7.648),('deadline_8',8),('deadline_10',10),('deadline_13',13)];summary=[];slots=[]
for arm,D in arms:
 rows=sorted([r for r in d['rows'] if r['task']['stage']=='primary' and r['task']['variant']==arm],key=lambda r:r['task']['frequency_hz']);assert len(rows)==14
 accepted=[r['task']['frequency_hz'] for r in rows if r['selected']=='pass'];rejected=[r['task']['frequency_hz'] for r in rows if r['selected']=='fail'];assert all(r['selected'] in ['pass','fail'] for r in rows);assert max(rejected)<min(accepted)
 row=dict(arm=arm,deadline_s=D,ideal_boundary_band_hz=[64000/D,96000/D],last_sampled_rejected_hz=max(rejected),first_sampled_accepted_hz=min(accepted),selected_pass=len(accepted),selected_fail=len(rejected),selected_skip=0,selected_missing=0,slow_faults_accepted=sum(r['selected']=='pass' and r['task']['frequency_hz']<17000 for r in rows),slow_faults_detected=sum(r['selected']=='fail' and r['task']['frequency_hz']<17000 for r in rows),legal_control_outcomes={str(r['task']['frequency_hz']):r['selected'] for r in rows if r['task']['frequency_hz'] in [17000,32000]},primary_record_sha256=[r['record_sha256'] for r in rows])
 for r in rows:
  hz=r['task']['frequency_hz'];pred='all_accept' if 96000/hz<=D else 'all_reject' if 64000/hz>D else 'phase_dependent';assert pred=='phase_dependent' or r['selected']==('pass' if pred=='all_accept' else 'fail')
  slots.append(dict(arm=arm,frequency_hz=hz,selected=r['selected'],ideal_class=pred,record_sha256=r['record_sha256'],**{k:r['counts'][k] for k in ['pass','fail','skip','missing']}))
 summary.append(row)
counts={s:dict(selected=dict(Counter(r['selected'] for r in d['rows'] if r['task']['stage']==s)),case_counts={k:sum(r['counts'][k] for r in d['rows'] if r['task']['stage']==s) for k in ['pass','fail','skip','missing']}) for s in ['nominal','primary','diagnostic_replay']}
result=dict(job_id='3598828',archive_sha256=d['archive']['archive_sha256'],verified_complete=True,counts=counts,arms=summary,replays=d['replay_comparisons'],phase_measured=False,actual_frequency_control_added=False,source_ideal_band_disagreements=0,all_phase_robustness_established=False,thresholds_are_sample_brackets_not_exact=True,prior_qualification_failure_retained=True)
(a.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
with (a.out/'primary_cells.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(slots[0]));w.writeheader();w.writerows(slots)
lines=[r'\begin{tabular}{@{}lrrr@{}}',r'\toprule',r'Wait/strategy & Ideal band & Observed bracket & Slow accepted\\',r' & (kHz) & (kHz) & /12\\',r'\midrule']
for r in summary:
 label=f"{r['deadline_s']:g} s"+(' poll' if r['arm']=='derived_poll' else '')
 lines.append(f"{label} & {r['ideal_boundary_band_hz'][0]/1000:.2f}--{r['ideal_boundary_band_hz'][1]/1000:.2f} & {r['last_sampled_rejected_hz']/1000:g}--{r['first_sampled_accepted_hz']/1000:g} & {r['slow_faults_accepted']} "+r'\\')
lines += [r'\bottomrule',r'\end{tabular}'];(a.out/'boundary_table.tex').write_text('\n'.join(lines)+'\n');print(json.dumps(counts,indent=2))
