#!/usr/bin/env python3
"""Derive the A–B before/after ledger without changing any frozen records."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from support import load_plan, read, save, sha

ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--bundle', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
repo = a.repo.resolve()
plan = load_plan(a.bundle)
assert plan['phase'] == 'AB'
old_path = repo / 'analysis/rtc_factorial_v2_final_summary.json'
old = {r['suite_id']: r for r in read(old_path)['suite_distribution']}
expected = {sid for sid, r in old.items() if r['status'] == 'prediction_only'}
assert expected == set(plan['versions']) and len(expected) == 16
records = defaultdict(dict)
for path in (repo / 'results/rtc_factorial_v2/records').glob('*-seeded-*.json'):
    r = read(path)
    if r['suite_id'] in old:
        assert r['seed'] not in records[r['suite_id']]
        records[r['suite_id']][r['seed']] = r
for sid, r in old.items():
    if sid in expected:
        assert not records[sid]
        continue
    counts = Counter(x['outcome'] for x in records[sid].values())
    assert len(records[sid]) == 100
    assert (counts['pass'], counts['fail'], 100-counts['pass']-counts['fail']) == (r['pass'], r['fail'], r['missing'])
before = {sid: dict(rs) for sid, rs in records.items()}
out = a.bundle / 'study' / plan['output_relative']
new_count = 0
for path in (out / 'records').glob('*.json'):
    r = read(path)
    v = plan['versions'][r['suite_id']]
    assert r['source_sha256'] == v['source_sha256'] and r['elf_sha256'] == v['elf_sha256']
    assert r['schedule_sha256'] == plan['schedule_sha256']
    for key in ('trace', 'uart', 'monitor'):
        if r.get(key+'_sha256'):
            assert sha(a.bundle/'study'/r[key+'_path']) == r[key+'_sha256']
    assert all(r.get(k) for k in ('node_name','container_sha256','slurm_job_id','apptainer_version'))
    new_count += 1
    if r['condition'] == 'seeded':
        assert r['seed'] not in records[r['suite_id']]
        records[r['suite_id']][r['seed']] = r
assert new_count == 1632 and all(len(rs) == 100 for rs in records.values())

def csv_rows(rel):
    with (repo/rel).open() as f:
        return list(csv.DictReader(f))

fault_path = 'analysis/rtc_quality_mutant_scores/rows.csv'
faults = {}
for r in csv_rows(fault_path):
    if r['suite_id'] not in old:
        continue
    path = repo/r['record_path']
    assert sha(path) == r['record_sha256']
    assert read(path)['outcome'] == r['outcome']
    faults[r['suite_id'], r['operator']] = r['kill'] == 'yes'
padding_path = 'analysis/rtc_padding_audit.csv'
padding = {r['suite_id']: r['over_padded'] for r in csv_rows(padding_path)}
forecast_path = 'analysis/rtc_threshold_sample_v2/forecast_table.csv'
forecasts = {r['run_id']: r for r in csv_rows(forecast_path) if r['prediction_status']=='clock_only_prediction'}
assert len(forecasts) == 30

def metrics(data, ids):
    measured = [sid for sid in ids if data.get(sid)]
    robust = [sid for sid in measured if all(r['outcome']=='pass' for r in data[sid].values())]
    both = [sid for sid in robust if faults[sid,'late'] and faults[sid,'nonarrival']]
    samples = [r for sid in measured for r in data[sid].values()]
    predicted = [sid for sid in measured if sid in forecasts]
    matches = failures = 0
    for sid in predicted:
        failed_seeds = {int(s) for s in forecasts[sid]['predicted_failure_seeds'].split(',') if s}
        for seed, r in data[sid].items():
            assert r['outcome'] in ('pass','fail')
            matches += (r['outcome']=='fail') == (seed in failed_seeds)
            failures += r['outcome']=='fail'
    return dict(eligible=len(ids), measured=len(measured), forecast_only=len(ids)-len(measured),
        seed_slots=len(samples), seeded_outcomes=dict(Counter(r['outcome'] for r in samples)),
        observed_flip_suites=sum(any(r['outcome']=='fail' for r in data[sid].values()) for sid in measured),
        confirmed_robust=len(robust), robust_and_two_faults=len(both),
        quality_confirmed=sum(padding[sid]=='no' for sid in both),
        predictable_measured=len(predicted), predictable_verdicts=100*len(predicted),
        forecast_matches=matches, predicted_subset_observed_failures=failures)

groups = {'all': list(old)}
for model in ('luna','sol','astra'):
    for condition in ('range_absent','range_present'):
        groups[model+'|'+condition] = [sid for sid,r in old.items() if (r['model'],r['prompt_condition'])==(model,condition)]
result = dict(scope='A–B only; D/E and paper changes pending Phase 3 review',
    sources={rel:sha(repo/rel) for rel in ('analysis/rtc_factorial_v2_final_summary.json',fault_path,padding_path,forecast_path)},
    new_plan_sha256=sha(a.bundle/'plan.json'),
    groups={k:dict(before=metrics(before,ids),after=metrics(records,ids)) for k,ids in groups.items()})
save(a.out,result)
print(json.dumps(result['groups']['all'],indent=2))
