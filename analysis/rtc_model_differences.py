#!/usr/bin/env python3
"""Post-result model-ID contrasts from immutable RTC analysis ledgers."""
import csv,itertools,json
from pathlib import Path
from scipy.stats import fisher_exact
R=Path(__file__).resolve().parents[1]
Q=json.loads((R/'analysis/rtc_stage_a_quant.json').read_text())['all_attempts']
C=json.loads((R/'analysis/rtc_factorial_v2_final_summary.json').read_text())['suite_distribution']
with (R/'analysis/rtc_quality_mutant_scores/rows.csv').open(newline='') as f:
 M={(x['suite_id'],x['operator']):x for x in csv.DictReader(f)}
O=json.loads((R/'results/rtc_alarm_offset_v1/analysis_summary.json').read_text())['rows']
cells=[]
for prompt in ('range_absent','range_present'):
 for model in ('luna','sol','astra'):
  q=[x for x in Q if x['model']==model and x['prompt']==prompt]
  c=[x for x in C if x['model']==model and x['prompt_condition']==prompt]
  measured=[x for x in c if x['status']=='measured']
  eligible=sum(x['eligible'] for x in q)
  robust=sum(x['robust_confirmed'] for x in q)
  both=sum(x['status']=='measured' and x.get('pass')==100 and
    M[(x['suite_id'],'late')]['kill']=='yes' and
    M[(x['suite_id'],'nonarrival')]['kill']=='yes' for x in c)
  slow=sum(M[(x['suite_id'],'late')]['kill']=='yes' for x in c)
  nonarrival=sum(M[(x['suite_id'],'nonarrival')]['kill']=='yes' for x in c)
  late_offset=[x for x in O if x['kind']=='ai' and x['model']==model and x['prompt_condition']==prompt and x['sign']==1]
  cells.append(dict(model=model,prompt=prompt,attempts=15,working=eligible,clock_robust_confirmed=robust,
    robust_slow_nonarrival_kills=both,measured_suites=len(measured),measured_any_flip=sum(x['fail']>0 for x in measured),
    slow_kills=slow,slow_evaluable=sum(M[(x['suite_id'],'late')]['kill'] in ('yes','no') for x in c),
    nonarrival_kills=nonarrival,nonarrival_evaluable=sum(M[(x['suite_id'],'nonarrival')]['kill'] in ('yes','no') for x in c),
    late_offset_kills=sum(x['status']=='kill' for x in late_offset),late_offset_evaluable=sum(x['status'] in ('kill','survive') for x in late_offset)))
tests=[]
for prompt in ('range_absent','range_present'):
 by={x['model']:x for x in cells if x['prompt']==prompt}
 for metric in ('working','clock_robust_confirmed','robust_slow_nonarrival_kills','measured_any_flip','slow_kills','late_offset_kills'):
  for a,b in itertools.combinations(('luna','sol','astra'),2):
   x,y=by[a],by[b]
   denx=x['measured_suites'] if metric=='measured_any_flip' else (x['slow_evaluable'] if metric=='slow_kills' else (x['late_offset_evaluable'] if metric=='late_offset_kills' else 15))
   deny=y['measured_suites'] if metric=='measured_any_flip' else (y['slow_evaluable'] if metric=='slow_kills' else (y['late_offset_evaluable'] if metric=='late_offset_kills' else 15))
   p=None if not denx or not deny else float(fisher_exact([[x[metric],denx-x[metric]],[y[metric],deny-y[metric]]],alternative='two-sided').pvalue)
   tests.append(dict(prompt=prompt,metric=metric,model_a=a,model_b=b,a_yes=x[metric],a_total=denx,b_yes=y[metric],b_total=deny,p_two_sided=p))
assert len(tests)==36
(R/'analysis/rtc_model_differences.json').write_text(json.dumps({'cells':cells,'fisher':tests},indent=2)+'\n')
for c in cells:print(c)
for t in tests:print(t['prompt'],t['metric'],t['model_a'],t['model_b'],round(t['p_two_sided'],6) if t['p_two_sided'] is not None else 'n/a')
