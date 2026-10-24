#!/usr/bin/env python3
"""Verify new raw artifacts and summarize; never update old analysis or paper."""
import argparse
from collections import Counter
from pathlib import Path
from support import load_plan, read, sha

ap = argparse.ArgumentParser()
ap.add_argument('--bundle', type=Path, required=True)
a = ap.parse_args()
p = load_plan(a.bundle)
study = a.bundle / 'study'
out = study / p['output_relative']
rows = [read(f) for f in sorted((out / 'records').glob('*.json'))]
for r in rows:
    for key in ('trace', 'uart', 'monitor'):
        if r.get(key + '_sha256') and sha(study / r[key + '_path']) != r[key + '_sha256']:
            raise RuntimeError('Raw output differs: ' + r['run_id'])
    for key in ('node_name', 'container_sha256', 'slurm_job_id', 'apptainer_version'):
        if not r.get(key):
            raise RuntimeError('Missing provenance: ' + key)
comparisons = [read(f) for f in sorted((out / 'forecast_comparisons').glob('*.json'))]
result = dict(phase=p['phase'], expected=len(p['tasks']), records=len(rows),
    outcomes=dict(Counter(r['outcome'] for r in rows)),
    forecast_evaluable=sum(c.get('evaluable', False) for c in comparisons),
    forecast_matches=sum(c.get('agrees') is True for c in comparisons),
    forecast_mismatches=[c for c in comparisons if c.get('agrees') is False],
    per_suite={sid: dict(records=sum(r['suite_id'] == sid for r in rows),
        outcomes=dict(Counter(r['outcome'] for r in rows if r['suite_id'] == sid))) for sid in p['versions']},
    stop_marker=read(out / 'STOP.json') if (out / 'STOP.json').exists() else None,
    complete=len(rows) == len(p['tasks']),
    next_action='STOP at Phase 3 before editing paper; repairs still require approval')
if p['phase'] == 'D':
    builds = [read(f) for f in (out / 'build_records').glob('*.json')]
    result['build_outcomes'] = dict(Counter(b['status'] for b in builds))
    result['tasks_accounted_for'] = len(builds)
import json
print(json.dumps(result, indent=2, sort_keys=True))
if result['stop_marker'] or (p['phase'] == 'AB' and not result['complete']):
    raise SystemExit(2)
