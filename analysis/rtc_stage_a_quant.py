#!/usr/bin/env python3
"""Stage A read-only derivations from frozen gate, clock, and fault records."""
import csv, json, math
from collections import defaultdict
from pathlib import Path
from scipy.stats import fisher_exact, binomtest

R=Path(__file__).resolve().parents[1]
def readcsv(p):
    with (R/p).open(newline='') as f:return list(csv.DictReader(f))
def readjson(p):return json.loads((R/p).read_text())
gates=readcsv('analysis/factorial_prephase3/model_condition_family.csv')
clock=readjson('analysis/rtc_factorial_v2_final_summary.json')['suite_distribution']
mut=readcsv('analysis/rtc_quality_mutant_scores/rows.csv')
pad=readcsv('analysis/rtc_padding_audit.csv')
off=readjson('results/rtc_alarm_offset_v1/analysis_summary.json')['rows']
cmap={x['suite_id']:x for x in clock}
mmap={(x['suite_id'],x['operator']):x for x in mut}
pmap={x['suite_id']:x for x in pad}
omap={(x['suite_id'],x['sign']):x for x in off}
family={'RTC callback':'rtc_alarm_callback','RTC pending':'rtc_alarm_pending','RTC counting':'rtc_time_counting'}
rows=[]
for g in gates:
    if g['task_family'] not in family:continue
    model,prompt,fam=g['model'],g['prompt_condition'],family[g['task_family']]
    suites=[x for x in clock if (x['model'],x['prompt_condition'],x['task_family'])==(model,prompt,fam)]
    robust=[x for x in suites if x['status']=='measured' and x['pass']==100]
    possible=[x for x in suites if x.get('fail',0)==0]
    strict=[x for x in robust if pmap[x['suite_id']]['over_padded']=='no' and
            mmap[(x['suite_id'],'late')]['kill']=='yes' and mmap[(x['suite_id'],'nonarrival')]['kill']=='yes']
    n=int(g['generated']);b=int(g['built']);f=int(g['source_functional_met']);e=int(g['functional_gate_eligible'])
    assert (n,len(suites))==(5,e)
    rows.append(dict(model=model,prompt=prompt,family=fam,attempts=n,build_fail=n-b,functional_fail=b-f,nominal_fail=f-e,eligible=e,
      measured_complete=len(robust),clock_flip=sum(x.get('fail',0)>0 for x in suites),
      clock_missing=sum(x['status']=='measured' and x.get('missing',0)>0 for x in suites),
      prediction_only=sum(x['status']=='prediction_only' for x in suites),
      robust_confirmed=len(robust),robust_possible=len(possible),
      quality_confirmed=len(strict),
      fast_kill=sum(mmap[(x['suite_id'],'early')]['kill']=='yes' for x in suites),
      slow_kill=sum(mmap[(x['suite_id'],'late')]['kill']=='yes' for x in suites),
      nonarrival_kill=sum(mmap[(x['suite_id'],'nonarrival')]['kill']=='yes' for x in suites),
      offset_early_kill=sum(omap.get((x['suite_id'],-1),{}).get('status')=='kill' for x in suites),
      offset_late_kill=sum(omap.get((x['suite_id'],1),{}).get('status')=='kill' for x in suites)))
assert len(rows)==18 and sum(x['eligible'] for x in rows)==66

# Suite-level Fisher tests. Unrun predictions are excluded. Missing seeded outcomes
# cannot establish a no-flip result; report both all-measured and complete-case.
fisher=[]
for fam in list(family.values())+['all']:
  for model in ['luna','sol','astra','all']:
    sub=[x for x in clock if x['status']=='measured' and (fam=='all' or x['task_family']==fam) and (model=='all' or x['model']==model)]
    counts=[]
    for prompt in ['range_absent','range_present']:
      s=[x for x in sub if x['prompt_condition']==prompt];counts.append((sum(x['fail']>0 for x in s),sum(x['fail']==0 for x in s),sum(x['missing']>0 for x in s)))
    if min(sum(v[:2]) for v in counts)==0: p=None
    else:p=fisher_exact([counts[0][:2],counts[1][:2]],alternative='two-sided').pvalue
    fisher.append(dict(family=fam,model=model,absent=counts[0],present=counts[1],p=p))

# Every measured AI suite is paired to the same upstream task at matching seeds.
records=R/'results/rtc_factorial_v2/records'
human={}; ai=defaultdict(dict)
for p in records.glob('*-seeded-*.json'):
  d=json.loads(p.read_text()); k=(d['family'],d['seed'])
  if d['kind']=='human':human[k]=d['outcome']
  elif d['kind']=='ai':ai[d['suite_id']][k]=d['outcome']
mcn=[]
for sid,ar in sorted(ai.items()):
  s=cmap[sid]; a=b=both_fail=both_pass=missing=0
  for k,v in ar.items():
    h=human[k]
    if v not in ('pass','fail') or h not in ('pass','fail'):missing+=1
    elif h=='fail' and v=='pass':a+=1
    elif h=='pass' and v=='fail':b+=1
    elif h=='fail':both_fail+=1
    else:both_pass+=1
  assert a+b+both_fail+both_pass+missing==100
  p=binomtest(min(a,b),a+b,.5).pvalue if a+b else 1.0
  mcn.append(dict(suite_id=sid,model=s['model'],prompt=s['prompt_condition'],family=s['task_family'],upstream_fail_ai_pass=a,upstream_pass_ai_fail=b,both_fail=both_fail,both_pass=both_pass,missing_pairs=missing,exact_p=p))
assert len(mcn)==50
out={'all_attempts':rows,'fisher':fisher,'mcnemar_per_suite':mcn}
(R/'analysis/rtc_stage_a_quant.json').write_text(json.dumps(out,indent=2)+'\n')
# Complete 13-task gate ledger: HSI factorial varied and mutant arms were deferred.
gate_rows=readjson('results/spec_context_factorial_v1/gate_summary.json')['rows']
by_task=defaultdict(list)
for x in gate_rows:by_task[(x['model'],x['condition'],x['task_id'])].append(x)
rtc_index={(x['model'],x['prompt'],x['family']):x for x in rows}
full=[]
for (model,prompt,task),items in sorted(by_task.items()):
 assert len(items)==5
 b=sum(x['build']=='pass' for x in items);f=sum(x['build']=='pass' and x['functional']=='met' for x in items)
 e=sum(x['amended_functional_eligible'] for x in items)
 q=rtc_index.get((model,prompt,task))
 full.append(dict(model=model,prompt=prompt,task=task,attempts=5,build_fail=5-b,functional_fail=b-f,nominal_fail=f-e,eligible=e,
  clock_status='rtc_results_in_companion_columns' if q else 'not_run',
  clock_flip=q['clock_flip'] if q else '',clock_complete_pass=q['measured_complete'] if q else '',
  clock_prediction_only=q['prediction_only'] if q else '',clock_zero_flip_missing=q['clock_missing'] if q else '',
  robust_confirmed=q['robust_confirmed'] if q else '',robust_possible=q['robust_possible'] if q else '',
  quality_confirmed=q['quality_confirmed'] if q else '',
  fast_kill=q['fast_kill'] if q else '',slow_kill=q['slow_kill'] if q else '',nonarrival_kill=q['nonarrival_kill'] if q else '',
  offset_early_kill=q['offset_early_kill'] if q and task!='rtc_time_counting' else '',
  offset_late_kill=q['offset_late_kill'] if q and task!='rtc_time_counting' else ''))
assert len(full)==78 and sum(x['eligible'] for x in full)==321
with (R/'analysis/stage_a_all_390_attempts.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(full[0]));w.writeheader();w.writerows(full)
for x in rows:print(x['model'],x['prompt'],x['family'],f"gate {x['build_fail']}/{x['functional_fail']}/{x['nominal_fail']}/{x['eligible']}",f"robust {x['robust_confirmed']}-{x['robust_possible']}/5",f"quality {x['quality_confirmed']}/5",f"faults {x['fast_kill']}/{x['slow_kill']}/{x['nonarrival_kill']}/{x['offset_early_kill']}/{x['offset_late_kill']}")
print('Fisher');[print(x) for x in fisher]
print('McNemar by family');
for fam in family.values():
 s=[x for x in mcn if x['family']==fam]
 print(fam,len(s),'discordances',sum(x['upstream_fail_ai_pass'] for x in s),sum(x['upstream_pass_ai_fail'] for x in s),'p<.05',sum(x['exact_p']<.05 for x in s),'missing',sum(x['missing_pairs'] for x in s))
