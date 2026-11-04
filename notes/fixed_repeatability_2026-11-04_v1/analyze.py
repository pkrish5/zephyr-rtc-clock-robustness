#!/usr/bin/env python3
"""One row for every preregistered repeat; missing observations are never filled."""
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--rtc',type=Path,required=True);p.add_argument('--counter',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
plan_path=HERE/'packet/plan.json';n=json.loads(plan_path.read_text());assert sha(plan_path)==(HERE/'packet/plan.sha256').read_text().split()[0]
roots={'f4-rtc':a.rtc/'output','f4-counter':a.counter/'output'}
verification={u:json.loads((base.parent/'verification.json').read_text()) for u,base in roots.items()}
rows=[];platform_by_cell=defaultdict(set)
for t in n['tasks']:
 base=roots[t['unit_id']];rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}";rp=base/'records'/(rid+'.json');mp=base/'repeat_metadata'/f"{t['index']:03d}.json"
 row=dict(index=t['index'],cell_id=t['cell_id'],case=t['selected_case'],frequency_hz=t['frequency_hz'],repeat_index=t['repeat_index'],selected_outcome='missing',observed_partial_selected='',reason='no primary record',job_id=verification[t['unit_id']]['job_id'],primary_record_sha256='',trace_sha256='',uart_sha256='',virtual_seconds='',host_wall_seconds='',kernel_reported_case_seconds='')
 if rp.exists():
  r=json.loads(rp.read_text());assert all(r[k]==v for k,v in t.items());info=n['unit_builds'][t['unit_id']]
  assert r['elf_sha256']==info['elf_sha256'] and r['build_record_sha256']==info['build_record_sha256']
  assert r['container_sha256']==n['image_sha256'] and r['slurm_job_id']==row['job_id']
  assert r['apptainer_module']=='tacc-apptainer/1.4.1' and r['launcher_module']=='launcher/3.10'
  assert r['apptainer_version'].startswith('apptainer version 1.4.1')
  assert rp.exists() and r['plan_sha256']==n['base_plan_sha256']
  for kind,h in r['log_sha256'].items():
   if h:assert sha(base/kind/(rid+('.json' if kind=='traces' else '.log')))==h
  platform=base/'platforms'/(rid+'.repl');assert sha(platform)==r['platform_sha256'];platform_by_cell[t['cell_id']].add(sha(platform))
  tr=json.loads((base/'traces'/(rid+'.json')).read_text())
  assert tr['run_id']==rid and tr['cases']==r['cases'] and tr['outcome']==r['outcome']
  assert platform.read_text()==f'using "/renode/platforms/boards/stm32f4_discovery.repl"\nrtc:\n    wakeupTimerFrequency: {t["frequency_hz"]}\nnvic:\n    systickFrequency: 16000000\n'
  monitor=(base/'monitor'/(rid+'.log')).read_text(errors='replace');assert 'cpu PerformanceInMips 16' in monitor
  # The frozen session fixes the quantum; verify its actual monitor command.
  assert '0.000001' in monitor and 'SetGlobalQuantum' in monitor
  cs=[c for c in r['cases'] if c['case']==t['selected_case']];row['observed_partial_selected']=';'.join(c['status'] for c in cs)
  row.update(primary_record_sha256=sha(rp),trace_sha256=r['log_sha256']['traces'],uart_sha256=r['log_sha256']['uart'],virtual_seconds=r['virtual_ns']/1e9,host_wall_seconds=r['wall_seconds'])
  if r['outcome']=='complete' and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'] and len(cs)==1 and mp.exists():
   m=json.loads(mp.read_text());assert m['primary_record_sha256']==sha(rp) and m['repeat_plan_sha256']==sha(plan_path) and m['protocol_sha256']==n['protocol_sha256']
   assert (m['cell_id'],m['repeat_index'],m['selected_case'],m['slurm_job_id'])==(t['cell_id'],t['repeat_index'],t['selected_case'],row['job_id'])
   assert [m[k] for k in ['cpu_mips','systick_hz','quantum_ns','step_ns']]==[16,16000000,1000,500000000]
   row.update(selected_outcome=cs[0]['status'],reason='explicit verdict in complete, error-free application')
  else:row['reason']=r.get('error') or 'incomplete/ambiguous application or missing provenance'
  uart=(base/'uart'/(rid+'.log')).read_text();d=re.search(r'\b(?:PASS|FAIL|SKIP) - '+re.escape(t['selected_case'].split('.')[-1])+r' in ([0-9.]+) seconds',uart)
  if d:row['kernel_reported_case_seconds']=d[1]
 rows.append(row)
assert len(rows)==180 and all(len(v)==1 for v in platform_by_cell.values())
cells=[]
for cell in [c['cell_id'] for c in json.loads((HERE/'input_verification.json').read_text())['cells']]:
 rr=[r for r in rows if r['cell_id']==cell];assert len(rr)==30;counts=Counter(r['selected_outcome'] for r in rr)
 mixed=bool(counts['pass'] and counts['fail']);concordant=max(counts.get(k,0) for k in ['pass','fail','skip'])==30
 cells.append(dict(cell_id=cell,case=rr[0]['case'],frequency_hz=rr[0]['frequency_hz'],pass_count=counts['pass'],fail_count=counts['fail'],skip_count=counts['skip'],missing_count=counts['missing'],observed_mixed_pass_fail=mixed,all_30_explicit_agree=concordant))
a.out.mkdir(parents=True,exist_ok=False)
for name,data in [('per_run.csv',rows),('per_cell.csv',cells)]:
 with (a.out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
summary=dict(planned_launches=180,counts=dict(Counter(r['selected_outcome'] for r in rows)),cells=cells,all_30_agree_in_every_cell=all(c['all_30_explicit_agree'] for c in cells),observed_mixed_pass_fail_cells=[c['cell_id'] for c in cells if c['observed_mixed_pass_fail']],rare_flakiness_ruled_out=False,no_original_records_replaced=True,archive_verification=verification)
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Fixed-setting repeatability results','', '|Case-frequency cell|Pass|Fail|Skip|Missing|','|---|---:|---:|---:|---:|']
for c in cells:lines.append('|'+c['cell_id']+'|'+'|'.join(str(c[k+'_count']) for k in ['pass','fail','skip','missing'])+'|')
lines+=['']
if summary['all_30_agree_in_every_cell']:lines+=['All30 fresh-process verdicts agree in every cell: **no observed same-setting flakiness** in these cells under this model. Rare flakiness is not ruled out.']
elif summary['observed_mixed_pass_fail_cells']:lines+=['Mixed pass/fail observed within fixed cells: '+', '.join(summary['observed_mixed_pass_fail_cells'])+'. Claims are limited to these cells after verifying all fixed inputs.']
else:lines+=['No mixed pass/fail was observed among evaluable outcomes, but missing/skip variation prevents claiming all30 agreed in every cell.']
lines+=['','Missing verdicts remain missing. Between-cell differences are timing sensitivity. Timelines are in TIMELINES.md; no callback-entry or phase timestamp was directly measured.']
(a.out/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))
