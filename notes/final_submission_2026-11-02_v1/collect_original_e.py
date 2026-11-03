#!/usr/bin/env python3
"""Compute-only read-only collection of original E evidence for reconciliation.

No build, simulation, source edit, deletion, or primary-record replacement.
Run only after the sealed recovery jobs have all finished.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    assert os.environ['SLURM_JOB_PARTITION'] == 'development'
    repo = Path(os.environ['RTC_REPO']).resolve()
    packet = repo / 'notes/e_resume_2026-11-02_v1/packet'
    jobs = ('3547925', '3547926', '3547927', '3547928', '3547929', '3547930', '3547931')
    status = subprocess.check_output(['sacct', '-X', '-n', '-P', '-j', ','.join(jobs),
                                      '--format=JobID,State'], text=True, timeout=30)
    states = {line.split('|')[0]: line.split('|')[1] for line in status.splitlines() if line.strip()}
    assert all(states.get(job) == 'COMPLETED' for job in jobs), states
    bundle = repo / 'tacc_work/20261024-repair-v1/e-bundle'
    output = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    output.relative_to(Path(os.environ['SCRATCH']).resolve())
    plan_path = bundle / 'plan.json'
    plan = read(plan_path)
    selection = read(packet / 'selection.json')
    assert sha(plan_path) == selection['source_plan_sha256']
    old = bundle / 'study' / plan['output_relative']
    execution = read(old / 'execution.json')
    assert sha(old / 'execution.json') == selection['execution_sha256']
    expected = dict(read(packet / 'old_verified_file_hashes.json'))

    def add(path, digest=None):
        path = Path(path)
        path.relative_to(bundle)
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('Expected regular source file: ' + str(path))
        relative = str(path.relative_to(bundle))
        actual = sha(path)
        if digest is not None and actual != digest:
            raise RuntimeError('Old evidence seal differs: ' + relative)
        if relative in expected and expected[relative] != actual:
            raise RuntimeError('Conflicting source hash: ' + relative)
        expected[relative] = actual

    add(plan_path, selection['source_plan_sha256'])
    add(bundle / 'plan.sha256')
    for relative, digest in plan['input_sha256'].items():
        add(bundle / relative, digest)
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json',
                 'tasks-controls.json', 'control_audit.json', 'd_prerequisite.json', 'STOP.json'):
        add(old / name)
    for vid, digest in execution['gate_summary_sha256'].items():
        add(old / 'gate_summaries' / (vid + '.json'), digest)
    for builds in execution['builds'].values():
        for built in builds.values():
            if built['status'] == 'pass':
                add(bundle / 'study' / built['elf_path'], built['elf_sha256'])
            if built.get('log_path'):
                add(bundle / 'study' / built['log_path'], built['log_sha256'])
    # These derived/reference files are checked from their raw records locally.
    # Collect every existing file in each named evidence directory, not only
    # successful references. No simulation result is filtered by its verdict.
    for folder in ('faults/scores', 'controls/scores', 'faults/replay_audit',
                   'legal/replay_audit', 'legal/reference_claims',
                   'legal/reference_results', 'legal/references'):
        source = old / folder
        if source.exists():
            for path in sorted(source.rglob('*')):
                if path.is_symlink():
                    raise RuntimeError('Unexpected evidence symlink: ' + str(path))
                if path.is_file():
                    add(path)
    for files in selection['partial_files'].values():
        for relative, digest in files.items():
            add(bundle / relative, digest)
    dest = output / 'original_bundle'

    def copy_item(item):
        relative, digest = item
        source = bundle / relative
        source.resolve().relative_to(bundle.resolve())
        if source.is_symlink() or sha(source) != digest:
            raise RuntimeError('Original changed before copy: ' + relative)
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        if sha(target) != digest:
            raise RuntimeError('Copied evidence differs: ' + relative)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(copy_item, sorted(expected.items())))
    for relative, digest in expected.items():
        if sha(bundle / relative) != digest:
            raise RuntimeError('Original changed during collection: ' + relative)
    save(output / 'job_metadata/original_e_files.sha256.json', expected)
    save(output / 'job_metadata/original_e_collection.json', dict(
        slurm_job_id=os.environ['SLURM_JOB_ID'], recovery_job_states=states,
        source_plan_sha256=sha(plan_path), source_execution_sha256=sha(old / 'execution.json'),
        expected_old_primary_records=selection['complete_and_valid'],
        preserved_finalized_harness_errors=selection['retained_harness_errors'],
        copied_verified_files=len(expected), source_files_rehashed_before_after=True,
        new_simulations=0, new_builds=0, original_records_modified=False,
        original_files_deleted=0))


if __name__ == '__main__':
    main()
