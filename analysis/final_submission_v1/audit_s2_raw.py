"""Check S2 table cells against archived primary, replay and reference records.

This is offline artifact verification, not a new experiment. Primary verdicts
and the existing post-result source classification are never changed.
"""
from collections import Counter, defaultdict
from pathlib import Path
from common import sha

ROOT = 'notes/s2_attribution_2026-10-31'
PRIMARY = ROOT + '/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1'
REPLAY = ROOT + '/returned-replays-3546149-20261102/verified/output'
REFERENCE = 'notes/s2_reference_2026-11-02_v1/verified-3547096-v1/output'


def audit(inputs, cases, links):
    ledger = inputs.json(ROOT + '/returned-3544535/audit/record_sha256.json')
    counts, frequencies, originals = defaultdict(Counter), defaultdict(lambda: defaultdict(list)), {}

    def record(relative, expected=None):
        path = inputs.use(relative)
        if expected:
            assert sha(path) == expected, relative
        r = inputs.json(relative)
        parent = str(Path(relative).parent.parent)
        for kind, digest in r['log_sha256'].items():
            if digest:
                suffix = '.json' if kind == 'traces' else '.log'
                assert sha(inputs.use(parent + '/' + kind + '/' + r['run_id'] + suffix)) == digest
        trace = inputs.json(parent + '/traces/' + r['run_id'] + '.json')
        assert trace['cases'] == r['cases'] and trace['error'] == r['error']
        return r

    for p in sorted(inputs.path(PRIMARY + '/records').glob('*.json')):
        rel = str(p.relative_to(inputs.root))
        key = 'results/s2_production_20261026_v1/records/' + p.name
        r = record(rel, ledger[key])
        assert r['application_completed'] and not r['error']
        originals[r['run_id']] = r
        for c in r['cases']:
            counts[r['unit_id'], c['case']][c['status']] += 1
            frequencies[r['unit_id'], c['case']][c['status']].append(r['frequency_hz'])
    assert len(originals) == 1122
    for row in cases:
        key = row['unit_id'], row['case']
        for status in ('pass', 'fail', 'skip'):
            assert counts[key][status] == int(row[status + '_count']), (key, status)
        assert sum(counts[key].values()) == 102 and int(row['missing_count']) == 0
        for status, adjective in [('fail', 'failed'), ('pass', 'passed')]:
            hz = frequencies[key][status]
            if hz:
                assert min(hz) == int(row['minimum_' + adjective + '_hz'])
                assert max(hz) == int(row['maximum_' + adjective + '_hz'])

    replay_count = 0
    equal = ('cases', 'application_completed', 'outcome', 'error', 'missing_cases', 'duplicate_cases',
             'elf_sha256', 'build_record_sha256', 'platform_sha256', 'renode_version', 'virtual_ns',
             'registers', 'rtc_divider_observations', 'suite_starts', 'reset_waits')
    for rid, r in originals.items():
        if not any(c['status'] == 'fail' for c in r['cases']):
            continue
        replay = record(REPLAY + '/records/' + rid + '.json')
        assert all(r.get(k) == replay.get(k) for k in equal), rid
        assert str(replay['slurm_job_id']) == '3546149'
        assert all(r['log_sha256'][k] == replay['log_sha256'][k] for k in ('traces', 'uart'))
        replay_count += 1
    assert replay_count == 274

    references, linked = {}, set()
    for row in links:
        rid, case = row['primary_run_id'], row['primary_case']
        assert (rid, case) not in linked
        linked.add((rid, case))
        assert any(c['case'] == case and c['status'] == 'fail' for c in originals[rid]['cases'])
        rp = PRIMARY + '/records/' + rid + '.json'
        assert sha(inputs.use(rp)) == row['original_primary_record_sha256']
        rrid = row['reference_run_id']
        if rrid not in references:
            references[rrid] = record(REFERENCE + '/records/' + rrid + '.json', row['reference_record_sha256'])
        ref = references[rrid]
        assert ref['application_completed'] and not ref['error']
        assert str(ref['slurm_job_id']) == '3547096'
        status = {c['case']: c['status'] for c in ref['cases']}
        assert ';'.join(status[c] for c in row['reference_cases'].split(';')) == row['reference_outcomes']
    assert len(linked) == 470
    return dict(primary_launches=1122, primary_case_slots=dict(sum(counts.values(), Counter())),
                identical_replay_launches=replay_count, linked_reference_failure_slots=len(linked),
                raw_records_checked=True, new_experiments=False)
