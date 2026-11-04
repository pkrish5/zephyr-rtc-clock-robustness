#!/usr/bin/env python3
"""Offline audit of the existing paired repairs and distinct expanded case names.

No firmware execution, new experiment, replacement verdict or frozen-input edit.
Run after make tables verifies the pinned publication archive.
"""
import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACKAGE = ROOT / 'notes/final_submission_2026-11-02_v1/phase3_package_v2'
VARIANTS = ['V0', 'V1', 'V1b', 'V2', 'V3']
OPS = ['fast', 'slow', 'nonarrival', 'offset_early', 'offset_late']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    rows = read_csv(PACKAGE / 'repair_primary_index.csv')
    assert len(rows) == 17375
    for row in rows:
        path = ROOT / row['record_path']
        assert sha(path) == row['record_sha256'], path
        data = json.loads(path.read_text())
        assert data['outcome'] == row['outcome'] and data['suite_id'] == row['version_id']
        if row['virtual_seconds']:
            assert float(row['virtual_seconds']) == data['virtual_ns'] / 1e9
    subject = lambda r: r['version_id'].rsplit('--', 1)[0]
    legal = {(subject(r), r['variant'], r['condition'], r['seed']): r for r in rows if r['operator'] == 'legal'}
    faults = {(subject(r), r['variant'], r['operator']): r for r in rows if r['operator'] != 'legal'}
    subjects = sorted({subject(r) for r in rows})
    assert len(subjects) == 33
    sensitive = sorted({subject(r) for r in rows if r['variant'] == 'V0' and r['operator'] == 'legal' and r['outcome'] == 'fail'})
    assert len(sensitive) == 6
    old_failure_keys = [(s, c, seed) for (s, v, c, seed), r in legal.items() if v == 'V0' and r['outcome'] == 'fail']
    assert len(old_failure_keys) == 112
    variants = []
    stored = {r['variant']: r for r in read_csv(PACKAGE / 'repair_per_variant.csv')}
    for v in VARIANTS:
        rr = [r for r in rows if r['variant'] == v]
        seeds = [r for r in rr if r['operator'] == 'legal' and r['condition'] == 'seeded']
        endpoints = [r for r in rr if r['operator'] == 'legal' and r['condition'] != 'seeded']
        result = dict(variant=v, seeded_fail=sum(r['outcome'] == 'fail' for r in seeds),
                      seeded_missing=sum(r['outcome'] not in ('pass', 'fail') for r in seeds),
                      endpoint_fail=sum(r['outcome'] == 'fail' for r in endpoints),
                      endpoint_missing=sum(r['outcome'] not in ('pass', 'fail') for r in endpoints),
                      median_simulated_seconds=median(float(r['virtual_seconds']) for r in seeds if r['outcome'] in ('pass', 'fail')))
        assert len(seeds) == 3300 and len(endpoints) == 66
        for field in ('seeded_fail', 'seeded_missing', 'endpoint_fail', 'endpoint_missing'):
            assert result[field] == int(stored[v][field])
        assert result['median_simulated_seconds'] == float(stored[v]['median_seeded_virtual_seconds'])
        for op in OPS:
            scored = [r for r in rr if r['operator'] == op and r['evaluable'] == 'True']
            detections = sum(r['detected'] == 'True' for r in scored)
            result[op] = dict(detected=detections, evaluable=len(scored))
            assert detections == int(stored[v][op + '_detected'])
            assert len(scored) == int(stored[v][op + '_evaluable'])
        subgroup = [r for r in rr if subject(r) in sensitive and r['operator'] == 'legal']
        result['six_sensitive_subjects_legal_outcomes'] = dict(Counter(r['outcome'] for r in subgroup))
        assert len(subgroup) == 612
        result['six_sensitive_subjects_slow'] = dict(Counter(faults[s, v, 'slow']['outcome'] for s in sensitive))
        result['V0_failed_slots_after_variant'] = dict(Counter(legal[s, v, c, seed]['outcome'] for s, c, seed in old_failure_keys))
        variants.append(result)
    paired = []
    for a, b in zip(VARIANTS, VARIANTS[1:]):
        for op in OPS:
            common = [(s, faults[s, a, op], faults[s, b, op]) for s in subjects
                      if (s, a, op) in faults and (s, b, op) in faults
                      and faults[s, a, op]['evaluable'] == faults[s, b, op]['evaluable'] == 'True']
            cells = Counter((x['detected'], y['detected']) for _, x, y in common)
            gained = [s for s, x, y in common if x['detected'] == 'False' and y['detected'] == 'True']
            lost = [s for s, x, y in common if x['detected'] == 'True' and y['detected'] == 'False']
            assert not lost
            paired.append(dict(before=a, after=b, operator=op, common_evaluable=len(common),
                               retained=cells['True', 'True'], both_missed=cells['False', 'False'],
                               gained=gained, lost=lost))
    gain = next(r for r in paired if (r['before'], r['after'], r['operator']) == ('V1', 'V1b', 'slow'))
    assert len(gain['gained']) == 11 and all(s not in sensitive and 'rtc_time_counting' in s for s in gain['gained'])
    polling = next(r for r in paired if (r['before'], r['after'], r['operator']) == ('V1b', 'V2', 'slow'))
    assert polling['common_evaluable'] == polling['retained'] == 32 and not polling['gained']
    duration = {}
    for v in VARIANTS:
        rr = [r for r in rows if subject(r) == 'human-rtc_alarm_callback' and r['variant'] == v
              and r['operator'] == 'legal' and r['condition'] == 'seeded' and r['outcome'] in ('pass', 'fail')]
        duration[v] = median(float(r['virtual_seconds']) for r in rr)
    assert duration['V1b'] == 42 and duration['V2'] == 20.75
    s2 = read_csv(PACKAGE / 's2_per_case_with_references.csv')
    by_name = defaultdict(list)
    for r in s2:
        by_name[r['case']].append(r)
    runnable = sorted(name for name, rs in by_name.items() if any(int(r['pass_count']) + int(r['fail_count']) for r in rs))
    assert len(by_name) == 19 and len(runnable) == 10
    categories = {c: sorted({r['case'] for r in s2 if r['category'] == c and int(r['fail_count'])}) for c in 'abcd'}
    assert [len(categories[c]) for c in 'abcd'] == [1, 3, 1, 1]
    result = dict(primary_record_hashes_checked=len(rows), primary_outcomes=dict(Counter(r['outcome'] for r in rows)),
                  sensitive_subjects=sensitive, variants=variants, adjacent_variant_pairs=paired,
                  upstream_callback_median_simulated_seconds=duration,
                  expanded_declared_distinct_case_names=19, expanded_runnable_distinct_case_names=runnable,
                  expanded_categories_by_distinct_name=categories,
                  no_new_experiments=True, within_setting_flakiness_claim=False,
                  inputs={name: sha(PACKAGE / name) for name in ('repair_primary_index.csv', 'repair_per_variant.csv', 's2_per_case_with_references.csv')})
    (HERE / 'paired_and_scope_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(primary_records_verified=len(rows), primary_outcomes=result['primary_outcomes'],
                          sensitive_subjects=len(sensitive), expanded_runnable_names=len(runnable),
                          right_sizing_slow_gains=len(gain['gained']), additional_polling_slow_gains=len(polling['gained']),
                          any_paired_detection_losses=False), indent=2))


if __name__ == '__main__':
    main()
