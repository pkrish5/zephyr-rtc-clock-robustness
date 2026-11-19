"""Read-only record audit. Missing stays missing; replays never replace primary."""
import hashlib,json,re
from collections import Counter
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def assess(out,plan,execution,stages):
 rows=[]
 for t in plan['tasks']:
  if t['stage'] not in stages:continue
  row=dict(task=t,integrity=False,selected='missing',counts={'pass':0,'fail':0,'skip':0,'missing':len(plan['units'][0]['expected_declared_cases'])})
  try:
   rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}";rp=out/'records'/(rid+'.json');r=json.loads(rp.read_text());row['record_sha256']=sha(rp)
   assert all(r[k]==v for k,v in t.items())
   assert r['natural_execution_sha256']==sha(out/'job_metadata/execution.json') and not r['phase_control'] and not r['observer']
   assert r['container_sha256']==execution['image_sha256'] and r['plan_sha256']==execution['plan_sha256'] and r['renode_version']==plan['renode_version']
   b=out/'builds'/t['unit_id'];br=json.loads((b/'build_record.json').read_text());assert sha(b/'build_record.json')==r['build_record_sha256'] and sha(b/'build/zephyr/zephyr.elf')==r['elf_sha256']==br['elf_sha256']
   assert br['status']=='built' and br['exit_code']==0 and br['source_commit']==plan['zephyr_commit'] and sha(b/'build.log')==br['log_sha256']
   for rel,h in br['build_products_sha256'].items():assert sha(b/'build'/rel)==h
   platform=out/'platforms'/(rid+'.repl');assert sha(platform)==r['platform_sha256']
   assert platform.read_text()==f'using "/renode/platforms/boards/{plan["boards"]["f4"]["platform"]}"\nrtc:\n    wakeupTimerFrequency: {t["frequency_hz"]}\nnvic:\n    systickFrequency: 16000000\n'
   for kind,suffix in [('uart','.log'),('monitor','.log'),('traces','.json')]:assert sha(out/kind/(rid+suffix))==r['log_sha256'][kind]
   text=(out/'uart'/(rid+'.log')).read_text();cases=[dict(case=c,status=s.lower()) for s,c in re.findall(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]',text)]
   assert cases==r['cases'];tr=json.loads((out/'traces'/(rid+'.json')).read_text());assert all(tr[k]==r[k] for k in ['cases','registers','application_completed','outcome','error'])
   row.update(integrity=True,cases=cases,missing_cases=r['missing_cases'],duplicate_cases=r['duplicate_cases'],outcome=r['outcome'],error=r['error'],process_exit=json.loads((out/'processes/run'/f"{t['index']}.json").read_text())['exit_code'],application_completed=r['application_completed'],wall_seconds=r['wall_seconds'],virtual_ns=r['virtual_ns'])
   row['counts']={s:sum(c['status']==s for c in cases) for s in ['pass','fail','skip']};row['counts']['missing']=len(r['missing_cases'])
   selected=[c['status'] for c in cases if c['case']=='counter_basic.test_all_channels'];row['selected']=selected[0] if len(selected)==1 else 'missing_or_duplicate'
   row['complete']=r['outcome']=='complete' and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'] and row['process_exit']==0 and Counter(c['case'] for c in cases)==Counter(r['expected_declared_cases'])
   row['normalized_trace_sha256']=hashlib.sha256(json.dumps({k:v for k,v in tr.items() if k!='run_id'},sort_keys=True,separators=(',',':')).encode()).hexdigest();row['uart_sha256']=r['log_sha256']['uart']
  except Exception as ex:row['audit_error']=type(ex).__name__+': '+str(ex)
  rows.append(row)
 nominal=[r for r in rows if r['task']['stage']=='nominal']
 qualified=len(nominal)==35 and all(r['integrity'] and r.get('complete') and r['selected']=='pass' and r['counts']['fail']==0 for r in nominal)
 replay=[]
 for r in rows:
  if r['task']['stage']!='diagnostic_replay':continue
  prim=next((x for x in rows if x['task']['stage']=='primary' and x['task']['unit_id']==r['task']['unit_id'] and x['task']['frequency_hz']==10000),None)
  replay.append(dict(unit_id=r['task']['unit_id'],agreement=bool(prim and all(x.get('integrity') and x.get('complete') for x in [prim,r]) and all(prim.get(k)==r.get(k) for k in ['cases','uart_sha256','normalized_trace_sha256']))))
 return dict(qualified=qualified,rows=rows,replay_comparisons=replay,primary_replaced_by_replay=False)
