#!/usr/bin/env python3
"""Local independent task/trace/score/replay/reference check of new E records.

Run after the unchanged archive verifier. No firmware execution, record
replacement, missing-outcome retry, or change to the sealed production code.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--verified', type=Path, required=True)
    ap.add_argument('--job', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.repo, a.verified, a.out = a.repo.resolve(), a.verified.resolve(), a.out.resolve()
    packet = a.repo / 'notes/e_resume_2026-11-02_v1/packet'
    recovery = read(packet / 'resume_plan.json')
    selection = read(packet / 'selection.json')
    original = read(packet / 'original-plan.json')
    execution = read(packet / 'original-execution.json')
    tasks = read(packet / 'original-tasks-evaluate.json')
    schedule_path = a.repo / 'subjects/phase3_rtc/plan.json'
    assert sha(schedule_path) == original['schedule_sha256']
    schedule = read(schedule_path)
    output = a.verified / 'output'
    proof = read(a.verified / 'verification.json')
    assert proof['job_id'] == a.job and proof['protected_files_unchanged'] == 30067
    assert proof['output_state'] == 'complete'
    setup = read(output / 'job_metadata/resume_setup.json')
    result = read(output / 'job_metadata/chunk_result.json')
    chunk_id = setup['chunk_id']
    chunk = recovery['chunks'][chunk_id]
    assert setup['slurm_job_id'] == result['slurm_job_id'] == a.job
    assert setup['indices'] == result['indices'] == chunk['indices']
    assert setup['original_finalized_records_retried'] == 0
    assert setup['original_evidence_files_checked'] == result['original_evidence_files_rechecked'] == 35708
    assert setup['original_builds_read_only'] and setup['original_metadata_read_only']
    assert setup['resume_plan_sha256'] == sha(packet / 'resume_plan.json')
    assert setup['code_manifest_sha256'] == sha(packet / 'resume_code.sha256.json')
    assert result['complete'] and not result['original_records_modified'] and result['new_builds'] == 0
    assert result['finalized_missing_outcomes_retained']
    assert not (output / 'STOP.json').exists()
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        assert sha(output / name) == sha(packet / ('original-' + name))

    def physical(relative):
        rel = Path(relative).relative_to(original['output_relative'])
        assert '..' not in rel.parts and not rel.is_absolute()
        return output / rel

    def audit_record(path, vid, operator, hz):
        r = read(path)
        assert str(r['slurm_job_id']) == a.job and r['slurm_partition'] == 'normal'
        assert r['container_sha256'] == recovery['image_sha256']
        assert r['apptainer_version'] in ('apptainer version 1.4.1', 'apptainer version 1.4.1-1.el8')
        assert r['apptainer_module'] == 'tacc-apptainer/1.4.1' and r['launcher_module'] == 'launcher/3.10'
        assert r['node_name'] and r['phase2_plan_sha256'] == recovery['original_plan_sha256']
        assert r['manifest_sha256'] == recovery['execution_sha256']
        assert r['suite_id'] == vid and r['operator'] == operator and r['lsi_frequency_hz'] == hz
        b = execution['builds'][vid]['nominal' if operator in ('legal', 'fast', 'slow') else operator]
        assert r['source_sha256'] == b['source_sha256'] and r['elf_sha256'] == b['elf_sha256']
        assert r['outcome'] in ('pass', 'fail', 'harness_error', 'timeout', 'unknown', 'skip')
        for kind in ('trace', 'uart', 'monitor'):
            digest = r.get(kind + '_sha256')
            if not digest:
                assert kind != 'trace'
                continue
            assert sha(physical(r[kind + '_path'])) == digest
        tr = read(physical(r['trace_path']))
        assert all(tr[k] == r[k] for k in ('run_id', 'cases', 'outcome', 'error'))
        return r, tr

    rows, replay_rows, reference_rows = [], [], []
    expected_files = set()
    result_records = {r['index']: r for r in result['records']}
    assert len(result_records) == len(chunk['indices'])
    for index in chunk['indices']:
        assert str(index) not in selection['completed_record_sha256']
        task = tasks[index]
        assert task['index'] == index
        vid, operator = task['version_id'], task['operator']
        if operator == 'legal':
            condition = task['condition']
            rid = vid + '-' + condition + ('-%03d' % task['seed'] if condition == 'seeded' else '')
            relative = Path('legal/records') / (rid + '.json')
            hz = schedule['seeded_frequencies_hz'][task['seed']] if condition == 'seeded' else schedule['endpoints_hz'][condition]
        else:
            rid = vid + '--' + operator
            relative = Path('faults/records') / (rid + '.json')
            hz = 64000 if operator == 'fast' else 10000 if operator == 'slow' else 32000
        process = read(output / 'processes/evaluate' / (str(index) + '.json'))
        assert process['index'] == index and process['chunk_id'] == chunk_id
        assert str(process['slurm_job_id']) == a.job and process['exit_code'] == 0
        path = output / relative
        r, tr = audit_record(path, vid, operator, hz)
        assert r['repair_version_id'] == vid and r['repair_variant'] == execution['versions'][vid]['variant']
        if operator == 'legal':
            # The frozen runner records seed=None at min/max endpoints even
            # though their task-list loop carries the unused index zero.
            expected_seed = task['seed'] if condition == 'seeded' else None
            assert r['condition'] == condition and r['seed'] == expected_seed, index
        expected_files.add(str(relative))
        assert result_records[index] == dict(index=index, record_relative=str(relative), record_sha256=sha(path), outcome=r['outcome'])
        row = dict(index=index, job_id=a.job, chunk_id=chunk_id, version_id=vid, operator=operator,
                   condition=task.get('condition'), seed=task.get('seed'), frequency_hz=hz,
                   physical_record=str(path.relative_to(a.repo)), record_sha256=sha(path),
                   outcome=r['outcome'], error=r['error'], node_name=r['node_name'])
        if operator != 'legal':
            score = read(output / 'faults/scores' / (rid + '.json'))
            uart = physical(r['uart_path']).read_text(errors='replace') if r.get('uart_sha256') else ''
            active = (('QUALITY_ALARM_OFFSET id=' in uart and
                       'sign=%d ' % (-1 if operator == 'offset_early' else 1) in uart)
                      if operator.startswith('offset_') else True)
            assert score == dict(version_id=vid, operator=operator, outcome=r['outcome'], active=active,
                                 detected=active and r['outcome'] == 'fail',
                                 evaluable=active and r['outcome'] in ('pass', 'fail'), record_sha256=sha(path))
            row['fault_score'] = score
        if r['outcome'] == 'fail':
            relative_replay = (Path('legal/replay_records') if operator == 'legal' else Path('faults/replays/records')) / (rid + '.json')
            replay, rt = audit_record(output / relative_replay, vid, operator, hz)
            fields = ('lsi_frequency_hz', 'observations', 'cases', 'outcome', 'error') if operator == 'legal' else ('observations', 'cases', 'delay_measurements', 'outcome', 'error')
            differences = [k for k in fields if tr[k] != rt[k]]
            replay_rows.append(dict(index=index, differences=differences,
                                    selected_fields_match=not differences,
                                    raw_trace_hash_matches=r['trace_sha256'] == replay['trace_sha256']))
            if operator == 'legal':
                family = execution['versions'][vid]['family']
                key = family + '-' + str(hz)
                ref_result = read(output / 'legal/reference_results' / (key + '.json'))
                ref_vid = 'reference-' + family
                ref_record_path = output / 'legal/references' / key / 'records' / (ref_vid + '-seeded-000.json')
                ref, _ = audit_record(ref_record_path, ref_vid, 'legal', hz)
                # The frozen worker enriches the saved record in write_new,
                # while reference_results embeds the returned core dictionary.
                inline = ref_result['record']
                added = {'apptainer_module', 'apptainer_version', 'container_sha256',
                         'launcher_module', 'node_name', 'operator', 'original_suite_id',
                         'phase2_plan_sha256', 'repair_variant', 'repair_version_id',
                         'slurm_job_id', 'slurm_partition'}
                assert set(ref) - set(inline) == added and set(inline) <= set(ref)
                assert all(ref[k] == value for k, value in inline.items())
                reference_rows.append(dict(index=index, reference_key=key, outcome=ref['outcome'],
                                           reference_record_sha256=sha(ref_record_path),
                                           flag='reference_pass' if ref['outcome'] == 'pass' else 'reference_did_not_pass_investigate_not_test_brittleness'))
        rows.append(row)
    actual_files = {str(p.relative_to(output)) for folder in ('legal/records', 'faults/records')
                    for p in (output / folder).glob('*.json')}
    assert actual_files == expected_files
    summary = dict(job_id=a.job, chunk_id=chunk_id, archive_sha256=proof['archive_sha256'],
                   verified_indices=len(rows), outcomes=dict(Counter(r['outcome'] for r in rows)),
                   outcomes_by_operator={op: dict(Counter(r['outcome'] for r in rows if r['operator'] == op))
                                         for op in sorted({r['operator'] for r in rows})},
                   protected_files_unchanged=30067, old_evidence_files_rechecked_before_after=35708,
                   original_finalized_records_retried=0, replay_count=len(replay_rows),
                   replay_mismatches=[r for r in replay_rows if not r['selected_fields_match']],
                   reference_trigger_slots=len(reference_rows),
                   reference_nonpasses=[r for r in reference_rows if r['outcome'] != 'pass'],
                   original_records_modified=False, new_builds=0,
                   finalized_missing_outcomes_retained=True)
    a.out.mkdir(parents=True, exist_ok=False)
    for name, value in [('summary.json', summary), ('per_index.json', rows),
                        ('replays.json', replay_rows), ('references.json', reference_rows)]:
        with (a.out / name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
