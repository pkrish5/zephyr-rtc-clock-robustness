#!/usr/bin/env python3
"""Compare returned S2 replays with their primary records; local analysis only.

Never runs a test or changes a record. A missing or mismatching replay is
reported separately and never replaces a primary verdict.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def compare(item, replay_out, primary_out, job):
    rid = item['primary_run_id']
    row = dict(run_id=rid, index=item['primary_task']['index'], unit_id=item['primary_task']['unit_id'],
               frequency_hz=item['primary_task']['frequency_hz'], condition=item['primary_task']['condition'],
               failed_cases=';'.join(item['failed_cases']))
    path = replay_out / 'records' / (rid + '.json')
    if not path.exists():
        return dict(row, status='missing', differences='no replay record')
    replay = json.loads(path.read_text())
    primary = json.loads((primary_out / 'records' / (rid + '.json')).read_text())
    differences = []
    if sha(primary_out / 'records' / (rid + '.json')) != item['primary_record_sha256']:
        differences.append('primary record hash')
    # Execution identity and verdict fields must be equal; provenance may not be.
    for key in ('cases', 'application_completed', 'outcome', 'error', 'missing_cases', 'duplicate_cases',
                'elf_sha256', 'build_record_sha256', 'platform_sha256', 'renode_version', 'virtual_ns',
                'registers', 'rtc_divider_observations', 'suite_starts', 'reset_waits'):
        if replay.get(key) != primary.get(key):
            differences.append(key)
    # Hash the returned files too, so a record cannot vouch for absent logs.
    for kind, expected in replay['log_sha256'].items():
        suffix = '.json' if kind == 'traces' else '.log'
        target = replay_out / kind / (rid + suffix)
        if expected and (not target.exists() or sha(target) != expected):
            differences.append('returned ' + kind + ' hash')
    for kind in ('traces', 'uart'):
        if replay['log_sha256'].get(kind) != primary['log_sha256'].get(kind):
            differences.append(kind + ' bytes')
    provenance = []
    if str(replay['slurm_job_id']) != job:
        provenance.append('slurm_job_id')
    if replay['slurm_partition'] != 'normal':
        provenance.append('slurm_partition')
    verdict_same = replay['cases'] == primary['cases'] and replay['outcome'] == primary['outcome']
    status = 'identical' if not differences else 'verdicts_match_details_differ' if verdict_same else 'verdict_mismatch'
    return dict(row, status=status, differences=';'.join(differences),
                provenance_problems=';'.join(provenance),
                monitor_bytes_equal=replay['log_sha256'].get('monitor') == primary['log_sha256'].get('monitor'),
                primary_wall_seconds=primary['wall_seconds'], replay_wall_seconds=replay['wall_seconds'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('proposal', 'replay_output', 'primary_output', 'out'):
        ap.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    ap.add_argument('--expected-job', required=True)
    a = ap.parse_args()
    proposal = json.loads(a.proposal.read_text())
    rows = [compare(t, a.replay_output, a.primary_output, a.expected_job) for t in proposal['tasks']]
    roster = {t['primary_run_id'] for t in proposal['tasks']}
    extra = sorted(p.stem for p in (a.replay_output / 'records').glob('*.json') if p.stem not in roster)
    fields = ['run_id', 'index', 'unit_id', 'frequency_hz', 'condition', 'failed_cases', 'status', 'differences',
              'provenance_problems', 'monitor_bytes_equal', 'primary_wall_seconds', 'replay_wall_seconds']
    a.out.mkdir(parents=True, exist_ok=False)
    with (a.out / 'replay_comparison.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    by_status = Counter(r['status'] for r in rows)
    failures = sum(len(r['failed_cases'].split(';')) for r in rows if r['status'] == 'identical')
    summary = dict(roster_launches=len(rows), status_counts=dict(by_status),
                   case_failures_in_identical_replays=failures,
                   case_failures_on_roster=proposal['primary_case_failures_covered'],
                   by_unit={u: dict(Counter(r['status'] for r in rows if r['unit_id'] == u))
                            for u in sorted({r['unit_id'] for r in rows})},
                   differences=dict(Counter(d for r in rows for d in r['differences'].split(';') if d)),
                   provenance_problems=dict(Counter(d for r in rows for d in r.get('provenance_problems', '').split(';') if d)),
                   records_outside_roster=extra, primary_verdicts_changed=0)
    with (a.out / 'replay_summary.json').open('x') as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
