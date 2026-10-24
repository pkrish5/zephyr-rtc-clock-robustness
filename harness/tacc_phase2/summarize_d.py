#!/usr/bin/env python3
"""Separate zero-fault implementations, reference controls, and missingness."""
import argparse
import json
from collections import Counter
from pathlib import Path
from support import load_plan, read, sha

ap = argparse.ArgumentParser()
ap.add_argument('--bundle', type=Path, required=True)
a = ap.parse_args()
p = load_plan(a.bundle)
out = a.bundle / 'study' / p['output_relative']
builds = {int(f.stem): read(f) for f in (out / 'build_records').glob('*.json')}
runs = {r['task_index']: r for r in (read(f) for f in (out / 'records').glob('*.json'))}
rows = []
for t in p['tasks']:
    b, r = builds.get(t['index']), runs.get(t['index'])
    for key in ('trace', 'uart', 'monitor'):
        if r and r.get(key + '_sha256') and sha(a.bundle / 'study' / r[key + '_path']) != r[key + '_sha256']:
            raise RuntimeError('Raw output differs')
    rows.append(dict(index=t['index'], suite_id=t['suite_id'], implementation=t['implementation'],
        kind=t['version']['kind'], model=t['version']['model'], prompt_condition=t['version']['prompt_condition'],
        family=t['version']['family'], build_status=b['status'] if b else 'missing_build_record',
        outcome=r['outcome'] if r else ('build_fail' if b and b['status'] != 'pass' else 'missing_run_record')))
keys = ('implementation', 'kind', 'model', 'prompt_condition', 'family')
groups = {}
for r in rows:
    k = '|'.join(str(r[x]) for x in keys)
    groups.setdefault(k, []).append(r['outcome'])
print(json.dumps(dict(expected=len(rows), built=len(builds), nominal_records=len(runs),
    outcomes=dict(Counter(r['outcome'] for r in rows)),
    groups={k: dict(Counter(v)) for k, v in groups.items()}, rows=rows,
    next_action='Review all control failures/missingness; STOP before E runs and paper edits'), indent=2))
