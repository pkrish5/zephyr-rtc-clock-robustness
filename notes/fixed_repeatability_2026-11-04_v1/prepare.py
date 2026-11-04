#!/usr/bin/env python3
"""Seal an independent repeatability packet from verified archived F4 records."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
inputs=json.loads((HERE/'input_verification.json').read_text())
assert len(inputs['cells'])==6 and all(c['repeats']==30 for c in inputs['cells'])
for p,h in inputs['inputs'].items():assert sha(ROOT/p)==h,p
counter_files={}
for folder in ['notes/counter_repair_2026-11-04_v1','harness/tacc_counter_repair']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:counter_files[str(p.relative_to(ROOT))]=sha(p)
save(HERE/'counter_inputs_before.json',counter_files)
mem=math.ceil(1.5*32*max(c['max_archived_rss_kib'] for c in inputs['cells']))
jobs={}
for unit,limit in [('f4-rtc','01:30:00'),('f4-counter','02:00:00')]:
 cs=[c for c in inputs['cells'] if c['unit_id']==unit]
 timeout=inputs['unit_builds'][unit]['unit']['wall_timeout_seconds']
 seconds=1.5*sum(30*c['max_archived_wall_seconds'] for c in cs)/32+timeout+900
 jobs[unit]=dict(partition='development',nodes=1,workers=32,launches=90,wall_limit=limit,task_wall_timeout_seconds=timeout,estimated_node_hours=round(seconds/3600,6),reservation_su_ceiling=1.5 if unit=='f4-rtc' else 2)
cost=dict(jobs=jobs,estimated_su=sum(j['estimated_node_hours'] for j in jobs.values()),reservation_su_ceiling=3.5,charge_rate_su_per_node_hour=1,min_billed_hours=.25,method='1.5 * sum(30 * cell archived maximum wall seconds) /32 + one task timeout tail +900s setup/audit/packing reserve',peak_rss_kib=max(c['max_archived_rss_kib'] for c in inputs['cells']),memory_budget_kib=mem,node_memory_gib=256,memory_limit_fraction=.8,source='https://docs.tacc.utexas.edu/hpc/6lonestar/running/',no_queue_wait_estimate=True)
assert mem<.8*256*1024*1024
save(HERE/'COST.json',cost)
print(json.dumps(cost,indent=2))
