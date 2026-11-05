#!/usr/bin/env python3
"""Independently audit one completed repeatability application; no new execution."""
import argparse,csv,hashlib,json,re,shlex
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--verified',type=Path,required=True);p.add_argument('--unit',choices=['f4-rtc','f4-counter'],required=True);p.add_argument('--job',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
original=ROOT/'notes/fixed_repeatability_2026-11-04_v1';plan_path=original/'packet/plan.json';n=json.loads(plan_path.read_text());assert sha(plan_path)=='9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613'
base=a.verified/'output';archive_check=json.loads((a.verified/'verification.json').read_text());assert archive_check['job_id']==a.job and archive_check['unit']==a.unit
assert sha(base/'job_metadata/plan.json')==sha(plan_path)
for stage in ['before','after']:
 g=json.loads((base/f'job_metadata/input_verification_{stage}.json').read_text());assert g['all_passed'] and g['counter_inputs_unchanged']
 if stage=='after':assert g['original_elf_hashes_unchanged']
 else:assert g['repeat_plan_sha256']==sha(plan_path)
source_info=json.loads((original/'input_verification.json').read_text());expected_version=source_info['renode_version'];info=n['unit_builds'][a.unit];tasks=[t for t in n['tasks'] if t['unit_id']==a.unit];assert len(tasks)==90
indices={t['index'] for t in tasks};joblines=(base/'launcher/jobfile').read_text().splitlines();assert len(joblines)==90
job_tokens=[shlex.split(line) for line in joblines];assert {int(x[-1]) for x in job_tokens}==indices
assert all(x[:2]==['bash','-l'] and x[2].endswith('/harness/tacc_fixed_repeatability/task.sh') and len(x)==4 for x in job_tokens)
assert {int(p.stem) for p in (base/'processes').glob('*.json')}<=indices
rows=[];case_rows=[];platforms=defaultdict(set);nodes=set()
for t in tasks:
 rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}";rp=base/'records'/(rid+'.json');mp=base/'repeat_metadata'/f"{t['index']:03d}.json";pp=base/'processes'/f"{t['index']}.json"
 row=dict(index=t['index'],cell_id=t['cell_id'],case=t['selected_case'],frequency_hz=t['frequency_hz'],repeat_index=t['repeat_index'],selected_outcome='missing',reason='no primary record',process_exit_code=None,primary_record_sha256=None,trace_sha256=None,uart_sha256=None,normalized_trace_sha256=None,virtual_seconds=None,host_wall_seconds=None,kernel_reported_case_seconds=None,first_uart_verdict_observation_virtual_seconds=None)
 if pp.exists():
  proc=json.loads(pp.read_text());assert proc['index']==t['index'] and proc['slurm_job_id']==a.job;row['process_exit_code']=proc['exit_code']
 if rp.exists():
  r=json.loads(rp.read_text());assert r['run_id']==rid and all(r[k]==v for k,v in t.items())
  assert r['elf_sha256']==info['elf_sha256'] and r['build_record_sha256']==info['build_record_sha256']
  assert r['plan_sha256']==n['base_plan_sha256'] and r['container_sha256']==n['image_sha256']
  assert r['renode_version']==expected_version and r['slurm_job_id']==a.job and r['slurm_partition']=='development'
  assert r['apptainer_module']=='tacc-apptainer/1.4.1' and r['launcher_module']=='launcher/3.10' and r['apptainer_version'].startswith('apptainer version 1.4.1')
  nodes.add(r['node_name'])
  for k,v in r['log_sha256'].items():
   if v:assert sha(base/k/(rid+('.json' if k=='traces' else '.log')))==v
  platform=base/'platforms'/(rid+'.repl');assert sha(platform)==r['platform_sha256'];platforms[t['cell_id']].add(sha(platform))
  assert platform.read_text()==f'using "/renode/platforms/boards/stm32f4_discovery.repl"\nrtc:\n    wakeupTimerFrequency: {t["frequency_hz"]}\nnvic:\n    systickFrequency: 16000000\n'
  monitor=(base/'monitor'/(rid+'.log')).read_text(errors='replace');assert 'cpu PerformanceInMips 16' in monitor and 'SetGlobalQuantum "0.000001"' in monitor
  tr=json.loads((base/'traces'/(rid+'.json')).read_text());assert tr['run_id']==rid and tr['cases']==r['cases'] and tr['outcome']==r['outcome'] and tr['error']==r['error']
  uart=(base/'uart'/(rid+'.log')).read_text(errors='replace')
  extracted=[dict(case=c,status=s.lower()) for s,c in re.findall(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]',uart)];assert extracted==r['cases']
  expected_cases=info['unit']['expected_declared_cases'];assert r['expected_declared_cases']==expected_cases
  selected=[c for c in r['cases'] if c['case']==t['selected_case']]
  case_rows.extend(dict(index=t['index'],cell_id=t['cell_id'],repeat_index=t['repeat_index'],case=c['case'],status=c['status'],is_selected=c['case']==t['selected_case']) for c in r['cases'])
  row.update(primary_record_sha256=sha(rp),trace_sha256=r['log_sha256']['traces'],uart_sha256=r['log_sha256']['uart'],virtual_seconds=r['virtual_ns']/1e9,host_wall_seconds=r['wall_seconds'],normalized_trace_sha256=hashlib.sha256(json.dumps({k:v for k,v in tr.items() if k!='run_id'},sort_keys=True,separators=(',',':')).encode()).hexdigest())
  if r['outcome']=='complete' and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'] and len(selected)==1 and mp.exists() and row['process_exit_code']==0:
   assert Counter(c['case'] for c in r['cases'])==Counter(expected_cases)
   m=json.loads(mp.read_text());assert m['primary_record_sha256']==sha(rp) and m['primary_record_path']==str(rp.relative_to(base))
   assert m['repeat_plan_sha256']==sha(plan_path) and m['protocol_sha256']==n['protocol_sha256']
   assert (m['cell_id'],m['repeat_index'],m['selected_case'],m['slurm_job_id'])==(t['cell_id'],t['repeat_index'],t['selected_case'],a.job)
   assert [m[k] for k in ['cpu_mips','systick_hz','quantum_ns','step_ns']]==[16,16000000,1000,500000000]
   row.update(selected_outcome=selected[0]['status'],reason='explicit selected verdict in complete verified application, process exit0')
  else:row['reason']=r['error'] or 'incomplete/ambiguous application, missing provenance or nonzero process exit'
  dur=re.search(r'\b(?:PASS|FAIL|SKIP) - '+re.escape(t['selected_case'].split('.')[-1])+r' in ([0-9.]+) seconds',uart)
  if dur:row['kernel_reported_case_seconds']=float(dur[1])
  obs=[o['virtual_ns']/1e9 for o in tr['observations'] if any(c['case']==t['selected_case'] for c in o['cases'])]
  if obs:row['first_uart_verdict_observation_virtual_seconds']=min(obs)
 rows.append(row)
assert all(len(v)==1 for v in platforms.values()) and len(nodes)<=1
assert {p.stem for p in (base/'records').glob('*.json')}=={f"{t['unit_id']}-{t['condition']}-{t['index']:03d}" for t in tasks if (base/'records'/f"{t['unit_id']}-{t['condition']}-{t['index']:03d}.json").exists()}
cells=[]
for hz in n['frequencies_hz'][a.unit]:
 rr=[r for r in rows if r['frequency_hz']==hz];assert len(rr)==30 and {r['repeat_index'] for r in rr}==set(range(30));counts=Counter(r['selected_outcome'] for r in rr)
 def span(k):
  v=[r[k] for r in rr if r[k] is not None];return [min(v),max(v)] if v else None
 cells.append(dict(cell_id=rr[0]['cell_id'],case=rr[0]['case'],frequency_hz=hz,pass_count=counts['pass'],fail_count=counts['fail'],skip_count=counts['skip'],missing_count=counts['missing'],mixed_pass_fail=bool(counts['pass'] and counts['fail']),all30_explicit_agree=max(counts.get(k,0) for k in ['pass','fail','skip'])==30,kernel_reported_case_seconds_span=span('kernel_reported_case_seconds'),sampled_uart_verdict_observation_virtual_seconds_span=span('first_uart_verdict_observation_virtual_seconds'),host_wall_seconds_span=span('host_wall_seconds'),unique_normalized_trace_count=len({r['normalized_trace_sha256'] for r in rr if r['normalized_trace_sha256']})))
summary=dict(job_id=a.job,unit=a.unit,status='verified',archive_state=archive_check['output_state'],archive_sha256=archive_check['archive_sha256'],scheduled=90,primary_records=sum(bool(r['primary_record_sha256']) for r in rows),evaluable=sum(r['selected_outcome']!='missing' for r in rows),counts=dict(Counter(r['selected_outcome'] for r in rows)),cells=cells,fixed_settings_verified=True,unique_nodes=sorted(nodes),all30_agree_each_cell=all(c['all30_explicit_agree'] for c in cells),observed_mixed_pass_fail_cells=[c['cell_id'] for c in cells if c['mixed_pass_fail']],rare_flakiness_ruled_out=False,protected_files_unchanged=30067,counter_inputs_unchanged=True,renode_version=expected_version,source_plan_sha256=sha(plan_path))
a.out.mkdir(parents=True,exist_ok=False)
for name,data in [('per_run.csv',rows),('all_case_verdicts.csv',case_rows)]:
 with (a.out/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Verified '+a.unit+' fixed-setting repeatability (partial study)','',f'Job {a.job}; 90 planned launches. Other application results are not included here.','', '|Fixed frequency, Hz|Pass|Fail|Skip|Missing|','|---:|---:|---:|---:|---:|']
for c in cells:lines.append('|'+str(c['frequency_hz'])+'|'+'|'.join(str(c[k+'_count']) for k in ['pass','fail','skip','missing'])+'|')
lines+=['']
if summary['all30_agree_each_cell']:lines+=['All 30 verdicts agree in each of these three cells: **no observed same-setting flakiness in this application at these settings**. Rare flakiness is not ruled out.']
else:lines+=['Mixed pass/fail cells: '+str(summary['observed_mixed_pass_fail_cells'])+'. Missing/skipped outcomes remain explicit; no claim of agreement across all 30 repeats.']
lines+=['','## Evidence-linked timing observations','', 'Kernel-reported case duration and sampled Renode UART exposure below are distinct measurements. Neither timestamps callback entry or subsecond phase. Full traces, UART and record hashes are listed per run.','', '|Frequency Hz|Kernel-reported case duration range, s|First sampled verdict exposure, virtual s|','|---:|---|---|']
for c in cells:lines.append('|'+str(c['frequency_hz'])+'|'+str(c['kernel_reported_case_seconds_span'])+'|'+str(c['sampled_uart_verdict_observation_virtual_seconds_span'])+'|')
lines+=['',f'Verified archived evidence: [{a.verified.name}]({a.verified.resolve()}). Source/inference timeline remains in [TIMELINES.md]({(original/"TIMELINES.md").resolve()}); it is not a direct event-time measurement.','Normalized trace differences can reflect UART visibility/rounding; they do not by themselves establish verdict flakiness.','']
(a.out/'REPORT.md').write_text('\n'.join(lines));print(json.dumps({k:v for k,v in summary.items() if k not in ['renode_version']},indent=2))
