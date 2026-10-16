#!/usr/bin/env python3
"""Deterministic source/profile similarity for the 66 eligible RTC suites."""
import csv,json,re
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def csvrows(p):
 with (R/p).open(newline='') as f:return list(csv.DictReader(f))
clock=json.loads((R/'analysis/rtc_factorial_v2_final_summary.json').read_text())['suite_distribution']
mut=csvrows('analysis/rtc_quality_mutant_scores/rows.csv')
off=json.loads((R/'results/rtc_alarm_offset_v1/analysis_summary.json').read_text())['rows']
mutmap={(x['suite_id'],x['operator']):x['kill'] for x in mut}
offmap={(x['suite_id'],x['sign']):x['status'] for x in off}
up={'rtc_alarm_callback':'test_alarm_callback.c','rtc_alarm_pending':'test_alarm.c','rtc_time_counting':'test_time_incrementing.c'}
base=R/'subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src'
cats=['eventual','not_before','exact_calendar','upper_bound','register_readback','count_id']
def strip(s):return re.sub(r'//[^\n]*|/\*.*?\*/',' ',s,flags=re.S)
def assertions(s):
 out=[]
 for m in re.finditer(r'\b(zassert_[A-Za-z0-9_]+)\s*\(',s):
  i=m.end();depth=1;quote=False;escape=False
  while i<len(s) and depth:
   c=s[i]
   if quote:
    if escape:escape=False
    elif c=='\\':escape=True
    elif c=='"':quote=False
   elif c=='"':quote=True
   elif c=='(':depth+=1
   elif c==')':depth-=1
   i+=1
  if depth==0:out.append((s.count('\n',0,m.start())+1,m.group(1),s[m.end():i-1]))
 return out
def classify(fn,arg):
 a=arg.lower(); tags=[]
 if re.search(r'pending|callback|called|fired|occur|elapsed|reached|increment|timeout|time.*limit',a):tags.append('eventual')
 if re.search(r'prematur|before|early|not.?pending|not.?called|not.?fired|too soon',a):tags.append('not_before')
 readback=bool(re.search(r'alarm_get_time|readback|alarm_time_get|alarm_read|mask_get|read.*alarm',a))
 if not readback and re.search(r'calendar_compare|target.*sec|tm_sec|tm_min|tm_hour|exact|configured rtc time',a):tags.append('exact_calendar')
 if re.search(r'deadline|timeout|ceiling|upper|late|after target|within|poll_limit|elapsed.*[<>]=?',a):tags.append('upper_bound')
 if readback:tags.append('register_readback')
 if re.search(r'count|_id\b|alarm id|channel|mask|user.data',a):tags.append('count_id')
 # API return checks and setup assertions are retained as other, never forced.
 return tags or ['other']
def apis(s):
 names=set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',strip(s)))
 return sorted(x for x in names if re.match(r'^(rtc_|k_|atomic_|counter_|device_is_ready$|timeutil_)',x) and not x.startswith('k_uptime_ticks'))
def grams(s):
 toks=re.findall(r'[A-Za-z_]\w*|0[xX][0-9A-Fa-f]+|\d+|==|!=|<=|>=|&&|\|\||[^\s]',strip(s))
 return set(tuple(toks[i:i+5]) for i in range(max(0,len(toks)-4)))
def jac(a,b):return len(a&b)/len(a|b) if a|b else 1.0
def profile(sid,fam):
 p={x:mutmap.get((sid,op)) for x,op in [('fast','early'),('slow','late'),('nonarrival','nonarrival')]}
 if fam!='rtc_time_counting':p.update(offset_early=offmap.get((sid,-1)),offset_late=offmap.get((sid,1)))
 return p
human_id={'rtc_alarm_callback':'human-rtc_alarm_callback','rtc_alarm_pending':'human-rtc_alarm_pending','rtc_time_counting':'human-rtc_time_counting'}
def cleanout(x):return {'yes':'kill','no':'survive'}.get(x,x)
oracle=[]; suites=[]
eligible={x['suite_id'] for x in clock}
for fam,name in up.items():
 hpath=base/name; hs=hpath.read_text(); ha=assertions(hs)
 for line,fn,arg in ha:oracle.append(dict(suite_id=human_id[fam],family=fam,kind='upstream',path=str(hpath.relative_to(R)),line=line,assertion=fn,expression=arg,categories=classify(fn,arg)))
 for spath in sorted((R/'generated/spec_context_factorial_v1/suites').glob(f'*/range_*/{fam}/r*/test.c')):
  model,prompt,_,rnum=spath.relative_to(R/'generated/spec_context_factorial_v1/suites').parts[:4]
  sid=f'{model}-{prompt}-{fam}-{rnum}'
  ss=spath.read_text();sa=assertions(ss)
  for line,fn,arg in sa:oracle.append(dict(suite_id=sid,family=fam,kind='llm',path=str(spath.relative_to(R)),line=line,assertion=fn,expression=arg,categories=classify(fn,arg)))
  hprof=profile(human_id[fam],fam);sprof=profile(sid,fam)
  comparable=[k for k in hprof if cleanout(hprof[k]) in ('kill','survive') and cleanout(sprof.get(k)) in ('kill','survive')]
  agreements=sum(cleanout(hprof[k])==cleanout(sprof[k]) for k in comparable)
  ac=Counter(t for _,f,a in sa for t in classify(f,a));hc=Counter(t for _,f,a in ha for t in classify(f,a))
  hp=set(apis(hs));ap=set(apis(ss));gg=grams(hs);ag=grams(ss)
  suites.append(dict(suite_id=sid,eligible=sid in eligible,model=model,prompt=prompt,family=fam,profile_agree=agreements,profile_comparable=len(comparable),profile_ai={k:cleanout(v) for k,v in sprof.items()},profile_upstream={k:cleanout(v) for k,v in hprof.items()},assertions=len(sa),oracle_counts=dict(ac),upstream_assertions=len(ha),upstream_oracle_counts=dict(hc),api_jaccard=jac(ap,hp),api_ai=sorted(ap),api_upstream=sorted(hp),surface_5gram_jaccard=jac(ag,gg)))
assert len(suites)==90 and sum(x['eligible'] for x in suites)==66
with (R/'analysis/rtc_stage_a_oracle_assertions.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['suite_id','family','kind','path','line','assertion','expression','categories']);w.writeheader();w.writerows([{**x,'categories':';'.join(x['categories']),'expression':x['expression'].replace('\n',' ')} for x in oracle])
(R/'analysis/rtc_stage_a_similarity.json').write_text(json.dumps(suites,indent=2)+'\n')
print('assertions',len(oracle),'suites',len(suites))
for model in ['luna','sol','astra']:
 for prompt in ['range_absent','range_present']:
  s=[x for x in suites if x['model']==model and x['prompt']==prompt]
  def mean(a):return round(sum(a)/len(a),3) if a else None
  a=Counter();[a.update(x['oracle_counts']) for x in s]
  print(model,prompt,'n',len(s),'eligible',sum(x['eligible'] for x in s),'profile',sum(x['profile_agree'] for x in s),'/',sum(x['profile_comparable'] for x in s),'api',mean([x['api_jaccard'] for x in s]),'surface',mean([x['surface_5gram_jaccard'] for x in s]),'max surface',max(x['surface_5gram_jaccard'] for x in s),'assertions',sum(x['assertions'] for x in s),'category',dict(a))
