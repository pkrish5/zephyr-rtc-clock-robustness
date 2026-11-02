#!/usr/bin/env python3
"""Check a new namespace; completed originals are checked, never overwritten."""
import os
from pathlib import Path
from setup_fixture import read, save, sha
from setup_resume import record_relative, verify_originals


repo = Path(os.environ['RTC_REPO']).resolve()
packet = repo / 'notes/e_resume_2026-11-02_v1/packet'
plan = read(packet / 'resume_plan.json')
chunk_id = int(os.environ['RTC_E_CHUNK'])
chunk = plan['chunks'][chunk_id]
output = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
setup = read(output / 'job_metadata/resume_setup.json')
bundle = Path(setup['original_bundle'])
old_plan = read(bundle / 'plan.json')
old = bundle / 'study' / old_plan['output_relative']
tasks = read(output / 'tasks-evaluate.json')
execution = read(output / 'execution.json')
assert setup['indices'] == chunk['indices']
assert setup['resume_plan_sha256'] == sha(packet / 'resume_plan.json')
assert sha(old / 'STOP.json') == setup['original_stop_sha256']
assert not (output / 'STOP.json').exists()
rows = []
for index in chunk['indices']:
    task = tasks[index]
    process = read(output / 'processes/evaluate' / (str(index) + '.json'))
    assert process['index'] == index and process['chunk_id'] == chunk_id
    assert process['slurm_job_id'] == os.environ['SLURM_JOB_ID'] and process['exit_code'] == 0
    path = output / record_relative(task)
    record = read(path)
    assert record['slurm_job_id'] == os.environ['SLURM_JOB_ID']
    assert record['container_sha256'] == plan['image_sha256']
    assert record['apptainer_module'] == 'tacc-apptainer/1.4.1'
    assert record['launcher_module'] == 'launcher/3.10'
    assert record['manifest_sha256'] == plan['execution_sha256']
    assert record['repair_version_id'] == task['version_id'] and record['operator'] == task['operator']
    assert record['outcome'] in ('pass', 'fail', 'harness_error', 'timeout', 'unknown', 'skip')
    built = execution['builds'][task['version_id']][
        'nominal' if task['operator'] in ('legal', 'fast', 'slow') else task['operator']]
    assert record['elf_sha256'] == built['elf_sha256'] and record['source_sha256'] == built['source_sha256']
    for kind in ('trace', 'uart', 'monitor'):
        digest = record.get(kind + '_sha256')
        if not digest:
            assert kind != 'trace'
            continue
        rel = Path(record[kind + '_path']).relative_to(old_plan['output_relative'])
        assert '..' not in rel.parts and sha(output / rel) == digest
    trace = read(output / Path(record['trace_path']).relative_to(old_plan['output_relative']))
    assert all(trace[k] == record[k] for k in ('run_id', 'outcome', 'error', 'cases'))
    rows.append(dict(index=index, record_relative=str(path.relative_to(output)),
                     record_sha256=sha(path), outcome=record['outcome']))
expected = {str(record_relative(tasks[i])) for i in chunk['indices']}
actual = {str(p.relative_to(output)) for folder in ('legal/records', 'faults/records')
          for p in (output / folder).glob('*.json')}
assert actual == expected
checked = verify_originals(bundle, packet, read(packet / 'selection.json'))
for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
    assert sha(output / name) == sha(packet / ('original-' + name))
save(output / 'job_metadata/chunk_result.json', dict(
    complete=True, chunk_id=chunk_id, indices=chunk['indices'], records=rows,
    finalized_missing_outcomes_retained=True, original_evidence_files_rechecked=checked,
    original_records_modified=False, new_builds=0, slurm_job_id=os.environ['SLURM_JOB_ID']))
