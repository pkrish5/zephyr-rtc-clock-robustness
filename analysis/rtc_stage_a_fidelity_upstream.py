#!/usr/bin/env python3
"""Existing reference duration check and source-only upstream pattern inventory."""
import csv,json,re,statistics
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
records=R/'results/rtc_reference_triage_access/records'
dur=[]; outcome=Counter()
for p in sorted(records.glob('*.json')):
 d=json.loads(p.read_text());outcome[(d['family'],d['condition'],d['outcome'])]+=1
 if d['family']!='rtc_alarm_callback' or d['condition'] not in ('seeded','min','max'):continue
 log=(R/d['uart_path']).read_text()
 m=re.search(r'PASS - test_alarm_callback in ([0-9.]+) seconds',log)
 if not m:continue
 observed=float(m.group(1));ideal=320000/d['lsi_frequency_hz']
 dur.append(dict(run_id=d['run_id'],seed=d['seed'],frequency_hz=d['lsi_frequency_hz'],ztest_duration_s=observed,ideal_arrival_s=ideal,residual_s=observed-ideal))
assert len(dur)>2
with (R/'analysis/rtc_stage_a_reference_durations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(dur[0]));w.writeheader();w.writerows(dur)
with (R/'analysis/upstream_timing_threshold_scan.csv').open(newline='') as f:scan=list(csv.DictReader(f))
source=[]
for x in scan:
 p=R/x['source_path'];s=p.read_text(errors='replace');
 # These are source-pattern flags, not semantic test-coverage judgments.
 event=bool(re.search(r'zassert_[^;]*(callback|pending|expired|fired|increment|timer|count)',s,re.I|re.S))
 window=bool(re.search(r'k_(?:m?sleep|busy_wait)|K_(?:MSEC|SECONDS|USEC)|k_sem_take|k_poll|k_timer_status_sync',s))
 polling=bool(re.search(r'for\s*\([^;]*;[^;]*;|while\s*\(',s)) and bool(re.search(r'rtc_get_time|rtc_alarm_is_pending|counter_get_value|k_timer_status_get',s))
 readback=bool(re.search(r'rtc_alarm_get_time|rtc_get_time|counter_get_value|k_timer_remaining_get',s))
 callback=bool(re.search(r'callback|ISR|IRQ',s,re.I))
 latency=bool(re.search(r'(callback|interrupt|ISR)[^;\n]{0,160}(latency|delay|elapsed|uptime)|(latency|elapsed|uptime)[^;\n]{0,160}(callback|interrupt|ISR)',s,re.I))
 thread_allowance=bool(re.search(r'latency_ticks\s*=|processing overhead is used',s,re.I))
 indirect_callback_deadline=bool(re.search(r'callback|alarm_cnt|top_handler_cnt',s,re.I) and re.search(r'k_busy_wait|k_sleep|k_msleep',s))
 source.append(dict(path=x['source_path'],family_root=x['family_root'],scan_status=x['status'],eventual_pattern=event,window_pattern=window,polling_pattern=polling,readback_pattern=readback,callback_or_interrupt_text=callback,explicit_delivery_latency_pattern=latency,thread_execution_latency_allowance=thread_allowance,indirect_callback_deadline_pattern=indirect_callback_deadline))
with (R/'analysis/rtc_stage_a_upstream_patterns.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(source[0]));w.writeheader();w.writerows(source)
print('reference duration n',len(dur),'freq minmax',min(x['frequency_hz'] for x in dur),max(x['frequency_hz'] for x in dur),'residual minmaxmedian',min(x['residual_s'] for x in dur),max(x['residual_s'] for x in dur),statistics.median(x['residual_s'] for x in dur))
print('reference outcomes',dict(outcome))
print('upstream patterns',len(source),{k:sum(x[k] for x in source) for k in ['eventual_pattern','window_pattern','polling_pattern','readback_pattern','callback_or_interrupt_text','explicit_delivery_latency_pattern','thread_execution_latency_allowance','indirect_callback_deadline_pattern']})
print('latency candidates',[x['path'] for x in source if x['explicit_delivery_latency_pattern']])
