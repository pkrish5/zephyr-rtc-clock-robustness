#!/usr/bin/env python3
"""Verify a returned reference archive and link outcomes to all primary failures.

Local analysis only. Never runs firmware, replaces verdicts, or modifies inputs.
"""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_text())


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def csv_save(p, rows):
    with p.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--returned', type=Path, required=True)
    ap.add_argument('--job', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    repo = a.repo.resolve()
    root = a.returned.resolve()
    stem = a.job + '-s2-reference'
    archive = root / (stem + '.tar.gz')
    receipt = read(root / (stem + '.json'))
    manifest_path = root / (stem + '.manifest.json.gz')
    assert sha(archive) == receipt['archive_sha256'] == (root / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(manifest_path) == receipt['manifest_sha256']
    assert receipt['slurm_job_id'] == a.job
    manifest = json.loads(gzip.decompress(manifest_path.read_bytes()))['files']
    assert len(manifest) == receipt['archive_entries']
    assert all(r['kind'] in ('file', 'directory') for r in manifest.values())
    spec = importlib.util.spec_from_file_location('s2_archive_verifier', repo / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.verify(archive, manifest)
    a.out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            p = a.out / member.name
            if member.isdir():
                p.mkdir(parents=True, exist_ok=True)
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, p.open('xb') as dest:
                    while block := source.read(1048576):
                        dest.write(block)
    output = a.out / 'output'
    assert helper.inventory(output) == manifest
    baseline = read(repo / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    for name in ('protected_before.json', 'protected_after.json'):
        r = read(output / 'job_metadata' / name)
        assert r['count'] == len(baseline) == 30067 and not r['changed']
        assert set(r['files']) == set(baseline)
        assert all(v['before_sha256'] == v['after_sha256'] == baseline[p] for p, v in r['files'].items())
    packet = repo / 'notes/s2_reference_2026-11-02_v1/packet'
    plan = read(packet / 'plan.json')
    setup = read(output / 'job_metadata/setup.json')
    assert setup['plan_sha256'] == sha(packet / 'plan.json')
    build_proofs = []
    for unit in plan['units']:
        path = output / 'builds' / unit['id'] / 'build_record.json'
        if not path.exists():
            continue
        b = read(path)
        assert str(b['slurm_job_id']) == a.job and b['container_sha256'] == plan['image_sha256']
        assert sha(path.parent / 'build.log') == b['log_sha256']
        if b['status'] == 'built':
            assert sha(path.parent / 'build/zephyr/zephyr.elf') == b['elf_sha256']
            for rel, expected in b['build_products_sha256'].items():
                assert sha(path.parent / 'build' / rel) == expected
        build_proofs.append(dict(unit_id=unit['id'], status=b['status'], build_record_sha256=sha(path)))
    records = {}
    for p in sorted((output / 'records').glob('*.json')):
        r = read(p)
        assert str(r['slurm_job_id']) == a.job and r['container_sha256'] == plan['image_sha256']
        assert r['plan_sha256'] == sha(packet / 'plan.json')
        for kind, expected in r['log_sha256'].items():
            suffix = '.json' if kind == 'traces' else '.log'
            if expected:
                assert sha(output / kind / (r['run_id'] + suffix)) == expected
        trace = read(output / 'traces' / (r['run_id'] + '.json'))
        assert trace['cases'] == r['cases'] and trace['error'] == r['error']
        assert r['run_id'] not in records
        records[r['run_id']] = r
    categories = {}
    previous = repo / 'notes/s2_attribution_2026-10-31/s2_report_20261102_v3/per_case.csv'
    for row in csv.DictReader(previous.open()):
        categories[(row['unit_id'], row['case'])] = row
    rows = []
    for task in plan['tasks']:
        if task['phase'] != 'evaluation':
            continue
        rid = f"{task['unit_id']}-{task['condition']}-{task['index']:03d}"
        r = records.get(rid)
        complete = bool(r and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'])
        statuses = {c['case']: c['status'] for c in r['cases']} if complete else {}
        for case in task['failed_cases']:
            primary = categories[(task['unit_id'], case)]
            refs = plan['reference_case_mapping'][case]
            outcomes = [statuses.get(c, 'missing') for c in refs]
            if 'missing' in outcomes or 'skip' in outcomes:
                flag = 'reference_missing_or_inapplicable_not_brittleness'
            elif 'fail' in outcomes:
                flag = 'firmware_or_simulator_investigation_not_test_brittleness'
            elif primary['category'] == 'c':
                flag = 'clean_state_reference_pass_original_cascade_not_independent_defect'
            elif primary['category'] == 'd':
                flag = 'reference_pass_accuracy_contract_and_phase_unresolved'
            else:
                flag = 'reference_supported_waiting_explanation_simulation_only'
            rows.append(dict(primary_run_id=task['primary_run_id'], primary_case=case,
                unit_id=task['unit_id'], board_role=primary['board_role'], frequency_hz=task['frequency_hz'],
                original_category=primary['category'], source_boundary=primary['source_boundary'],
                observed_primary_status='fail', original_primary_record_sha256=task['primary_record_sha256'],
                reference_run_id=rid, reference_cases=';'.join(refs), reference_outcomes=';'.join(outcomes),
                reference_record_sha256=sha(output / 'records' / (rid + '.json')) if r else '',
                reference_trace_sha256=r['log_sha256']['traces'] if r else '', flag=flag,
                phase_explanation='supported but not directly measured' if primary['category'] == 'b' else ''))
    assert len(rows) == plan['primary_failure_slots_covered'] == 470
    csv_save(a.out / 'primary_failure_reference_links.csv', rows)
    summary = dict(job_id=a.job, archive_sha256=sha(archive), output_state=receipt['output_state'],
        archive_entries_verified=len(manifest), protected_files_unchanged=30067,
        build_proofs=build_proofs, reference_records=len(records), linked_primary_failure_slots=len(rows),
        flags=dict(Counter(r['flag'] for r in rows)),
        by_board={b: dict(Counter(r['flag'] for r in rows if r['unit_id'].split('-')[0] == b))
                  for b in plan['board_roles']}, board_roles=plan['board_roles'],
        original_records_replaced=0, new_experiments_run_by_analysis=0)
    save(a.out / 'reference_validation_summary.json', summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
