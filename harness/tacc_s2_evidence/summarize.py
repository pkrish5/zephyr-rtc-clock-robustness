#!/usr/bin/env python3
"""Summarize a verified S2 archive locally; no experiment execution or submission."""
import argparse
import collections
import csv
import hashlib
import json
import shutil
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def table(p, rows):
    with p.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--evidence', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    e, out = a.evidence, a.out
    manifest = json.loads((e/'files.sha256.json').read_text())
    for rel, digest in manifest.items():
        if sha(e/rel) != digest:
            raise RuntimeError('Evidence hash differs: '+rel)
    plan = json.loads((e/'plan.json').read_text())
    report = json.loads((e/'raw/qualification_report.json').read_text())
    raw = e/'raw'
    rows = [json.loads(p.read_text()) for p in sorted((raw/'records').glob('*.json'))]
    by_index = {r['index']: r for r in rows}
    if len(by_index) != len(rows):
        raise RuntimeError('Duplicate task record')
    out.mkdir(parents=True, exist_ok=False)
    unfinished, omitted = [], []
    for t in plan['tasks']:
        if t['index'] in by_index:
            continue
        rid = f"{t['unit_id']}-{t['condition']}-{t['index']:03d}"
        if (raw/'not_attempted'/(rid+'.json')).exists():
            omitted.append(t)
        else:
            unfinished.append(dict(**t, evidence_state=(
                'started_without_final_record' if (raw/'stdout/run'/f"{t['index']}.log").exists()
                else 'not_started_before_job_timeout')))
    table(out/'unfinished_calibration.csv', unfinished)
    save(out/'omitted_after_nominal_gate.json', omitted)
    units = []
    costs = []
    for u in report['units']:
        cases = [c for c in csv.DictReader((raw/'per_case_qualification.csv').open()) if c['unit_id']==u['unit_id']]
        statuses = collections.Counter(c['nominal_classification'] for c in cases)
        units.append(dict(unit_id=u['unit_id'], nominal_working_cases=statuses['working'],
            nominal_skipped_cases=statuses['capability_skip'],
            nominal_missing_cases=statuses['missing_nominal'],
            nominal_failed_cases=statuses['nominal_failure'],
            nominal_complete=u['all_nominal_applications_complete'],
            calibration_completed_launches=u['calibration_launches'],
            calibration_required_launches=7, qualified_for_review=u['configuration_ready_for_review'],
            observed_dividers='/'.join(map(str,u['observed_dividers'])),
            maximum_wall_seconds=u['max_wall_seconds'], maximum_rss_bytes=u['max_peak_rss_bytes']))
        if u['qualified_cases']:
            costs.append(dict(unit_id=u['unit_id'], primary_application_launches=102,
                per_launch_case_verdict_slots=u['declared_cases'],
                currently_qualified=u['configuration_ready_for_review'],
                max_observed_wall_seconds=u['max_wall_seconds'],
                unrounded_su=102*u['max_wall_seconds']/32/3600*1.5))
    table(out/'configuration_summary.csv', units)
    shutil.copyfile(raw/'per_case_qualification.csv', out/'per_case_qualification.csv')
    ready = [r for r in costs if r['currently_qualified']]
    scenarios = dict(assumption='1 node; 32 workers; 102 full-application launches per configuration; max observed wall *1.5 safety; no builds, replays or references included',
        currently_ready=dict(configurations=[r['unit_id'] for r in ready],
            application_launches=sum(r['primary_application_launches'] for r in ready),
            case_verdict_slots=sum(102*r['per_launch_case_verdict_slots'] for r in ready),
            estimated_su=sum(r['unrounded_su'] for r in ready)),
        conditional_on_finishing_calibration=dict(configurations=[r['unit_id'] for r in costs],
            application_launches=sum(r['primary_application_launches'] for r in costs),
            case_verdict_slots=sum(102*r['per_launch_case_verdict_slots'] for r in costs),
            estimated_su=sum(r['unrounded_su'] for r in costs)),
        per_configuration=costs, production_submission_authorized=False)
    save(out/'production_cost_scenarios.json', scenarios)
    save(out/'verification.json', dict(evidence_files_verified=len(manifest),
        plan_sha256=sha(e/'plan.json'), raw_records=len(rows),
        raw_outcomes=dict(collections.Counter(r['outcome'] for r in rows)),
        not_attempted_by_gate=len(omitted),
        started_without_record=sum(t['evidence_state']=='started_without_final_record' for t in unfinished),
        not_started_before_timeout=sum(t['evidence_state']=='not_started_before_job_timeout' for t in unfinished),
        new_experiments=0, original_records_modified=False, summary_script_sha256=sha(Path(__file__))))
    print(json.dumps(scenarios, indent=2))


if __name__=='__main__':
    main()
