"""No-Renode union of original and independently verified recovery records."""
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from common import sha, wilson


RECOVERY = 'notes/e_resume_2026-11-02_v1'


def primary_relative(task):
    if task['operator'] == 'legal':
        rid = task['version_id'] + '-' + task['condition']
        if task['condition'] == 'seeded':
            rid += '-%03d' % task['seed']
        return Path('legal/records') / (rid + '.json')
    return Path('faults/records') / (task['version_id'] + '--' + task['operator'] + '.json')


def build(inputs, original_verified, chunk_verified):
    packet = RECOVERY + '/packet/'
    plan = inputs.json(packet + 'original-plan.json')
    execution = inputs.json(packet + 'original-execution.json')
    tasks = inputs.json(packet + 'original-tasks-evaluate.json')
    selection = inputs.json(packet + 'selection.json')
    recovery = inputs.json(packet + 'resume_plan.json')
    source_proof = inputs.json(original_verified + '/verification.json')
    assert source_proof['output_state'] == 'complete' and source_proof['protected_files_unchanged'] == 30067
    old_output = Path(original_verified) / 'output'
    old_bundle = old_output / 'original_bundle'
    old_study = old_bundle / 'study'
    old_records = old_study / plan['output_relative']
    collected = inputs.json(str(old_output / 'job_metadata/original_e_collection.json'))
    assert collected['expected_old_primary_records'] == 7824 and collected['preserved_finalized_harness_errors'] == 29
    assert not collected['original_records_modified'] and collected['source_files_rehashed_before_after']
    assert collected['new_simulations'] == collected['new_builds'] == collected['original_files_deleted'] == 0
    source_hashes = inputs.json(str(old_output / 'job_metadata/original_e_files.sha256.json'))
    original_hashes = inputs.json(packet + 'old_verified_file_hashes.json')
    assert set(original_hashes) <= set(source_hashes)
    assert all(source_hashes[k] == v for k, v in original_hashes.items())
    for relative, digest in source_hashes.items():
        assert sha(inputs.use(str(old_bundle / relative))) == digest
    assert sha(inputs.use(str(old_bundle / 'plan.json'))) == recovery['original_plan_sha256']
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        assert sha(inputs.use(str(old_records / name))) == sha(inputs.use(packet + 'original-' + name))
    assert execution['nominal_gate_passed'] == 165 and not execution['skips']
    for vid, digest in execution['gate_summary_sha256'].items():
        p = str(old_records / 'gate_summaries' / (vid + '.json'))
        assert sha(inputs.use(p)) == digest
        gate = inputs.json(p)
        assert gate['gate_pass'] and len(gate['nominal_outcomes']) == 5
        assert all(r['outcome'] == 'pass' for r in gate['nominal_outcomes'])
    for builds in execution['builds'].values():
        for built in builds.values():
            if built['status'] == 'pass':
                assert sha(inputs.use(str(old_study / built['elf_path']))) == built['elf_sha256']
    controls = inputs.json(str(old_records / 'control_audit.json'))
    assert controls['validated'] and len(controls['rows']) == 19
    assert all(r['validated'] for r in controls['rows'])
    schedule = inputs.json('subjects/phase3_rtc/plan.json')
    ownership = {int(i): (old_records, digest, 'old') for i, digest in selection['completed_record_sha256'].items()}
    assert len(chunk_verified) == len(recovery['chunks']) == 7
    for number, verified in enumerate(chunk_verified):
        proof = inputs.json(verified + '/verification.json')
        output = Path(verified) / 'output'
        summary = inputs.json(str(output / 'job_metadata/chunk_result.json'))
        setup = inputs.json(str(output / 'job_metadata/resume_setup.json'))
        assert proof['output_state'] == 'complete' and proof['protected_files_unchanged'] == 30067
        assert summary['complete'] and summary['chunk_id'] == number
        assert summary['indices'] == recovery['chunks'][number]['indices']
        assert summary['original_evidence_files_rechecked'] == setup['original_evidence_files_checked'] == 35708
        assert setup['original_finalized_records_retried'] == 0 and not summary['original_records_modified']
        assert setup['resume_plan_sha256'] == sha(inputs.use(packet + 'resume_plan.json'))
        for r in summary['records']:
            assert r['index'] not in ownership
            ownership[r['index']] = (output, r['record_sha256'], str(proof['job_id']))
    assert set(ownership) == set(range(len(tasks))) and len(tasks) == 17375

    def checked_record(output, relative, expected_vid=None, operator=None, hz=None):
        path = str(output / relative)
        r = inputs.json(path)
        assert r['container_sha256'] == recovery['image_sha256']
        assert r['phase2_plan_sha256'] == recovery['original_plan_sha256']
        assert r['manifest_sha256'] == recovery['execution_sha256']
        assert r['node_name'] and r['slurm_job_id']
        assert r['apptainer_module'] == 'tacc-apptainer/1.4.1' and r['launcher_module'] == 'launcher/3.10'
        assert r['apptainer_version'] in ('apptainer version 1.4.1', 'apptainer version 1.4.1-1.el8')
        if expected_vid is not None:
            assert r['suite_id'] == expected_vid and r['operator'] == operator and r['lsi_frequency_hz'] == hz
            b = execution['builds'][expected_vid]['nominal' if operator in ('legal', 'fast', 'slow') else operator]
            assert r['elf_sha256'] == b['elf_sha256'] and r['source_sha256'] == b['source_sha256']
        for kind in ('trace', 'uart', 'monitor'):
            if r.get(kind + '_sha256'):
                local = output / Path(r[kind + '_path']).relative_to(plan['output_relative'])
                assert '..' not in local.parts and sha(inputs.use(str(local))) == r[kind + '_sha256']
        trace = inputs.json(str(output / Path(r['trace_path']).relative_to(plan['output_relative'])))
        assert all(r[k] == trace[k] for k in ('run_id', 'outcome', 'error', 'cases'))
        return r, trace

    primary, replay_checks, reference_checks = [], [], []
    for task in tasks:
        index, vid, operator = task['index'], task['version_id'], task['operator']
        output, digest, job = ownership[index]
        path = output / primary_relative(task)
        assert sha(inputs.use(str(path))) == digest
        hz = ((schedule['seeded_frequencies_hz'][task['seed']] if task['condition'] == 'seeded' else schedule['endpoints_hz'][task['condition']])
              if operator == 'legal' else 64000 if operator == 'fast' else 10000 if operator == 'slow' else 32000)
        r, tr = checked_record(output, primary_relative(task), vid, operator, hz)
        assert r['repair_version_id'] == vid
        if operator == 'legal':
            assert r['condition'] == task['condition']
            assert r['seed'] == (task['seed'] if task['condition'] == 'seeded' else None)
        if job != 'old':
            assert str(r['slurm_job_id']) == job
        row = dict(index=index, version_id=vid, variant=execution['versions'][vid]['variant'],
                   family=execution['versions'][vid]['family'], operator=operator,
                   condition=task.get('condition'), seed=task.get('seed'), frequency_hz=hz,
                   outcome=r['outcome'], error=r['error'], virtual_seconds=r['virtual_ns'] / 1e9,
                   record_path=str(path), record_sha256=digest, job_id=str(r['slurm_job_id']))
        if operator != 'legal':
            score_path = output / 'faults/scores' / (r['run_id'] + '.json')
            score = inputs.json(str(score_path))
            uart = inputs.text(str(output / Path(r['uart_path']).relative_to(plan['output_relative']))) if r.get('uart_sha256') else ''
            active = (('QUALITY_ALARM_OFFSET id=' in uart and
                       'sign=%d ' % (-1 if operator == 'offset_early' else 1) in uart)
                      if operator.startswith('offset_') else True)
            assert score == dict(version_id=vid, operator=operator, outcome=r['outcome'], active=active,
                                 detected=active and r['outcome'] == 'fail',
                                 evaluable=active and r['outcome'] in ('pass', 'fail'), record_sha256=digest)
            row.update(active=active, detected=score['detected'], evaluable=score['evaluable'])
        if r['outcome'] == 'fail':
            replay_path = (Path('legal/replay_records') if operator == 'legal' else Path('faults/replays/records')) / (r['run_id'] + '.json')
            again, trace_again = checked_record(output, replay_path, vid, operator, hz)
            fields = ('lsi_frequency_hz', 'observations', 'cases', 'outcome', 'error') if operator == 'legal' else ('observations', 'cases', 'delay_measurements', 'outcome', 'error')
            replay_checks.append(dict(index=index, persisted_fields_match=all(tr[k] == trace_again[k] for k in fields),
                                      raw_trace_hash_matches=r['trace_sha256'] == again['trace_sha256']))
            if operator == 'legal':
                key = row['family'] + '-' + str(hz)
                reference_path = Path('legal/references') / key / 'records' / ('reference-' + row['family'] + '-seeded-000.json')
                ref, _ = checked_record(output, reference_path, 'reference-' + row['family'], 'legal', hz)
                reference_checks.append(dict(index=index, outcome=ref['outcome'], source_namespace=str(output),
                                              key=key, flag='reference_pass' if ref['outcome'] == 'pass' else
                                              'firmware_or_simulator_investigation_not_test_brittleness'))
        primary.append(row)
    assert len(primary) == len({r['index'] for r in primary}) == 17375
    assert not any(not r['persisted_fields_match'] for r in replay_checks), 'Phase A replay mismatch: stop, do not run Phase B'
    old_indices = set(map(int, selection['completed_record_sha256']))
    assert sum(r['outcome'] == 'harness_error' and r['index'] in old_indices for r in primary) == 29
    by_version = defaultdict(list)
    for r in primary:
        by_version[r['version_id']].append(r)
    variant_rows, subject_rows = [], []
    for vid, v in plan['versions'].items():
        rr = by_version[vid]
        seeded = [r for r in rr if r['operator'] == 'legal' and r['condition'] == 'seeded']
        endpoints = [r for r in rr if r['operator'] == 'legal' and r['condition'] != 'seeded']
        assert len(seeded) == 100 and len(endpoints) == 2
        valid = [r['virtual_seconds'] for r in seeded if r['outcome'] in ('pass', 'fail')]
        subject_rows.append(dict(version_id=vid, original_suite_id=v['original_suite_id'], variant=v['variant'],
                                 family=v['family'], seeded_fail=sum(r['outcome'] == 'fail' for r in seeded),
                                 seeded_missing=sum(r['outcome'] not in ('pass', 'fail') for r in seeded),
                                 endpoint_fail=sum(r['outcome'] == 'fail' for r in endpoints),
                                 endpoint_missing=sum(r['outcome'] not in ('pass', 'fail') for r in endpoints),
                                 confirmed_robust_100=all(r['outcome'] == 'pass' for r in seeded),
                                 median_seeded_virtual_seconds=median(valid) if valid else None))
    for variant in ('V0', 'V1', 'V1b', 'V2', 'V3'):
        rr = [r for r in primary if r['variant'] == variant]
        seeded = [r for r in rr if r['operator'] == 'legal' and r['condition'] == 'seeded']
        endpoints = [r for r in rr if r['operator'] == 'legal' and r['condition'] != 'seeded']
        subjects = [r for r in subject_rows if r['variant'] == variant]
        legal_valid = [r['virtual_seconds'] for r in seeded if r['outcome'] in ('pass', 'fail')]
        row = dict(variant=variant, subjects=33, gate_passed=33,
                   seeded_fail=sum(r['outcome'] == 'fail' for r in seeded),
                   seeded_missing=sum(r['outcome'] not in ('pass', 'fail') for r in seeded),
                   endpoint_fail=sum(r['outcome'] == 'fail' for r in endpoints),
                   endpoint_missing=sum(r['outcome'] not in ('pass', 'fail') for r in endpoints),
                   subjects_with_any_legal_failure=sum(r['seeded_fail'] + r['endpoint_fail'] > 0 for r in subjects),
                   confirmed_robust_100=sum(r['confirmed_robust_100'] for r in subjects),
                   median_seeded_virtual_seconds=median(legal_valid) if legal_valid else None,
                   median_duration_sample_size=len(legal_valid))
        for operator in ('fast', 'slow', 'nonarrival', 'offset_early', 'offset_late'):
            faults = [r for r in rr if r['operator'] == operator]
            n = sum(r['evaluable'] for r in faults)
            detected = sum(r['detected'] for r in faults)
            durations = [r['virtual_seconds'] for r in faults if r['evaluable']]
            row.update({operator + '_detected': detected, operator + '_evaluable': n,
                        operator + '_missing_or_inactive': len(faults) - n,
                        operator + '_wilson95': wilson(detected, n),
                        operator + '_median_virtual_seconds': median(durations) if durations else None})
        variant_rows.append(row)
    return dict(per_variant=variant_rows, per_subject=subject_rows, primary=primary,
                replay_checks=replay_checks, reference_checks=reference_checks,
                outcomes=dict(Counter(r['outcome'] for r in primary)),
                missing_policy='finalized missing outcomes retained; diagnostic replays do not replace primary scores',
                duration_definition='median virtual_ns / 1e9 among evaluable seeded legal-clock primary runs; endpoints, faults, diagnostics and harness errors excluded',
                original_records_replaced=0, new_simulations_run_by_analysis=0)
