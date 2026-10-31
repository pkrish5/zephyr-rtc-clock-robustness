#!/usr/bin/env python3
"""Prepare full-application replay tasks from independently verified S2 evidence.

Metadata analysis only. Never executes firmware, changes the primary plan, or
substitutes a replay for a primary verdict. Refuses record-only audit reports.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def prepare(evidence, audit, dest):
    verification = json.loads((audit / 'return_verification.json').read_text())
    report = json.loads((audit / 'report.json').read_text())
    if not report['raw_log_and_elf_hashes_verified']:
        raise RuntimeError('Full returned evidence must pass the independent audit first')
    required = {'report.json', 'record_sha256.json', 'per_case.csv',
                'per_board.csv', 'primary_failures.csv'}
    if not required <= set(verification['independent_audit_files_matching']):
        raise RuntimeError('Independent audit is incomplete')
    if report['missing_indices'] or report['records_with_error']:
        raise RuntimeError('Unexpected primary missingness requires review')
    bundle = evidence / 'bundle'
    primary = json.loads((bundle / 'plan.json').read_text())
    if sha(bundle / 'plan.json') != report['plan_sha256']:
        raise RuntimeError('Primary plan differs')
    output = bundle / primary['output_relative']
    records = {r['index']: (r, path) for path in (output / 'records').glob('*.json')
               for r in [json.loads(path.read_text())]}
    if set(records) != {task['index'] for task in primary['tasks']}:
        raise RuntimeError('Primary record roster differs')
    tasks = []
    by_unit = Counter()
    runtime = 0.0
    for task in primary['tasks']:
        record, path = records[task['index']]
        failures = [case['case'] for case in record['cases'] if case['status'] == 'fail']
        if not failures:
            continue
        if record['outcome'] != 'complete' or record['error']:
            raise RuntimeError('An incomplete primary launch cannot enter the failure replay roster')
        if any(record[key] != value for key, value in task.items()):
            raise RuntimeError('Task and primary record disagree')
        tasks.append(dict(primary_task=task, primary_record_sha256=sha(path),
                          primary_trace_sha256=record['log_sha256']['traces'],
                          primary_run_id=record['run_id'], failed_cases=failures,
                          primary_case_vector=record['cases'],
                          saved_wall_seconds=record['wall_seconds']))
        by_unit[record['unit_id']] += 1
        runtime += record['wall_seconds']
    observed_failures = sum(len(t['failed_cases']) for t in tasks)
    if observed_failures != report['case_slot_counts']['fail']:
        raise RuntimeError('Replay roster does not cover every primary assertion failure')
    value = dict(kind='S2 full-application failure replay proposal',
                 production_authorized=False, new_experiments_executed=0,
                 source_primary_job_id='3535524',
                 source_primary_plan_sha256=report['plan_sha256'],
                 source_evidence_archive_sha256=verification['archive_sha256'],
                 source_return_verification_sha256=sha(audit / 'return_verification.json'),
                 primary_case_failures_covered=observed_failures,
                 full_application_launches=len(tasks), launches_by_unit=dict(by_unit),
                 saved_total_worker_wall_seconds=round(runtime, 3),
                 suggested_concurrency=32,
                 throughput_estimated_node_hours_with_1_5_margin=round(runtime * 1.5 / 32 / 3600, 4),
                 estimation_limits='Saved primary runtimes; excludes queue wait, input audits, '
                                   'packing and filesystem slowdown. Not a Slurm reservation estimate.',
                 unchanged_simulation_worker_sha256=primary['conditional_approval_evidence']
                     ['unchanged_simulation_worker_sha256'],
                 comparison=['selected-case vector', 'application completion and error',
                             'persisted trace SHA-256', 'registers and observations'],
                 skips_retained=True, original_records_replaced=False,
                 replay_mismatch_policy='Report separately; do not rerun or replace a primary verdict',
                 tasks=tasks)
    dest.mkdir(parents=True, exist_ok=False)
    save(dest / 'replay_proposal.json', value)
    with (dest / 'replay_proposal.json.sha256').open('x') as stream:
        stream.write(sha(dest / 'replay_proposal.json') + '  replay_proposal.json\n')
    return {key: value[key] for key in ('full_application_launches',
            'primary_case_failures_covered', 'launches_by_unit',
            'throughput_estimated_node_hours_with_1_5_margin')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('evidence', 'audit', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.evidence, args.audit, args.out), indent=2))
