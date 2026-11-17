"""Shared fail-closed qualification checks; no mutation of raw evidence."""
import hashlib,json,re
from pathlib import Path
from collections import Counter
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(d):return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k!='run_id'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def timing(text,target,hz):
 events=[{'kind':k,'ns':int(ns),'ssr':int(ssr)} for k,ns,ssr in re.findall(r'^BOUNDARY_OBS\|(case_entry|read_before|read_after|callback)\|(\d+)\|(\d+)\s*$',text,re.M)]
 assert events and all(0<=x['ssr']<=249 for x in events)
 assert all(x['ns']<=y['ns'] for x,y in zip(events,events[1:]))
 starts=[i for i,x in enumerate(events) if x['kind']=='case_entry'];assert len(starts)==1
 selected=events[starts[0]+1:];i=next(i for i,x in enumerate(selected) if x['kind']=='read_before');before=selected[i];after=selected[i+1];assert after['kind']=='read_after'
 cb=next(x for x in selected[i+2:] if x['kind']=='callback')
 phi=(249-before['ssr'])/250;endphi=(249-after['ssr'])/250;period=32000/hz
 assert endphi>=phi and endphi-phi<=.02 and (after['ns']-before['ns'])/1e9<=.02*period
 assert max(abs(phi-target),abs(endphi-target))<=.020000001
 actual=(cb['ns']-before['ns'])/1e9;predicted=(3-phi)*period;tolerance=.02*period+.020
 assert abs(actual-predicted)<=tolerance
 return {'phase_before':phi,'phase_after':endphi,'target':target,'arrival_s':actual,'predicted_from_achieved_phase_s':predicted,'predicted_from_requested_phase_s':(3-target)*period,'error_s':actual-predicted,'tolerance_s':tolerance,'events':events}
def assess(out,plan,execution,stages):
 rows=[];pairs={}
 for t in plan['tasks']:
  if t['stage'] not in stages:continue
  row={'index':t['index'],'stage':t['stage'],'passed':False,'unit_id':t['unit_id'],'frequency_hz':t['frequency_hz'],'phase_hundredths':t['phase_hundredths'],'observer':t['observer']}
  try:
   rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}";rp=out/'records'/(rid+'.json');r=json.loads(rp.read_text());row.update(cases=r['cases'],missing_cases=r['missing_cases'],outcome=r['outcome'],record_sha256=sha(rp))
   assert all(r[k]==v for k,v in t.items())
   assert json.loads((out/'processes/run'/f"{t['index']}.json").read_text())['exit_code']==0
   assert r['outcome']=='complete' and not r['error'] and not r['missing_cases'] and not r['duplicate_cases']
   assert Counter(c['case'] for c in r['cases'])==Counter(r['expected_declared_cases'])
   folder=out/'builds'/t['unit_id'];br=folder/'build_record.json';elf=folder/'build/zephyr/zephyr.elf';hp=folder/'hooks.json'
   assert sha(br)==r['build_record_sha256'] and sha(elf)==r['elf_sha256'] and sha(hp)==r['hooks_sha256']
   assert r['phase_execution_sha256']==sha(out/'job_metadata/execution.json')
   assert r['renode_version']==plan['renode_version']
   assert r['container_sha256']==execution['image_sha256'] and r['plan_sha256']==execution['plan_sha256']
   platform=out/'platforms'/(rid+'.repl');assert sha(platform)==r['platform_sha256']
   assert f"wakeupTimerFrequency: {t['frequency_hz']}" in platform.read_text() and 'systickFrequency: 16000000' in platform.read_text()
   paths={k:out/k/(rid+('.json' if k=='traces' else '.log')) for k in ['uart','monitor','traces']}
   for k,path in paths.items():assert sha(path)==r['log_sha256'][k]
   trace=json.loads(paths['traces'].read_text())
   assert trace['cases']==r['cases'] and trace['outcome']==r['outcome'] and trace['error']==r['error']
   assert trace['application_completed']==r['application_completed']
   uart=paths['uart'].read_text()
   pattern=r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]' if t['stage']=='nominal' else r'\b(PASS|FAIL|SKIP) - (test_all_channels) in [0-9.]+ seconds'
   assert [{'case':c,'status':v.lower()} for v,c in re.findall(pattern,uart)]==r['cases']
   assert r['registers']==trace['registers'] and r['registers'][0]['rtc_prer']==(127<<16|249)
   row['normalized_trace_sha256']=normalized(trace);row['uart_sha256']=sha(paths['uart'])
   if t['stage']=='nominal':
    assert r['application_completed'] and r['completion_scope']=='full_application'
    assert all(c['status'] in ['pass','skip'] for c in r['cases'])
    assert any(c['case']=='counter_basic.test_all_channels' and c['status']=='pass' for c in r['cases'])
    pairs.setdefault((t['unit_id'],t['phase_hundredths']),{})[t['observer']]=row
   else:
    assert r['selected_diagnostic_completed'] and not r['application_completed'] and r['downstream_not_evaluated']
    assert r['cases']==[{'case':'test_all_channels','status':'pass'}]
   if t['observer']=='on':row['timing']=timing(paths['monitor'].read_text(),t['phase_hundredths']/100,t['frequency_hz'])
   row['passed']=True
  except Exception as ex:row['error']=type(ex).__name__+': '+str(ex)
  rows.append(row)
 pair_results=[]
 for key,p in pairs.items():
  passed=set(p)=={'off','on'} and all(v['passed'] for v in p.values())
  if passed:passed=all(p['off'][k]==p['on'][k] for k in ['cases','normalized_trace_sha256','uart_sha256'])
  pair_results.append({'unit_id':key[0],'phase_hundredths':key[1],'passed':passed})
 expected_pairs=21 if 'nominal' in stages else 0
 return {'passed':all(x['passed'] for x in rows) and all(x['passed'] for x in pair_results) and len(pair_results)==expected_pairs,'rows':rows,'pairs':pair_results,'primary_sweep_run':False}
