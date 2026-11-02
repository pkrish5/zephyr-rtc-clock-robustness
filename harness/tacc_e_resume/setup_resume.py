#!/usr/bin/env python3
"""Storage-only setup for exact audited E retry chunks; never rebuild inputs."""
import math
import os
from pathlib import Path
import shlex
from setup_fixture import read, save, sha


def verify_originals(bundle, packet, selection):
    if sha(packet / 'old_verified_file_hashes.json') != selection['old_verified_files_sha256']:
        raise RuntimeError('Original evidence ledger differs')
    verified = read(packet / 'old_verified_file_hashes.json')
    for rel, digest in verified.items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Original completed evidence differs: ' + rel)
    for index, files in selection['partial_files'].items():
        for rel, digest in files.items():
            if sha(bundle / rel) != digest:
                raise RuntimeError('Original interrupted evidence differs: ' + index)
    return len(verified)


def record_relative(task):
    if task['operator'] == 'legal':
        rid = task['version_id'] + '-' + task['condition']
        if task['condition'] == 'seeded':
            rid += '-%03d' % task['seed']
        return Path('legal/records') / (rid + '.json')
    return Path('faults/records') / (task['version_id'] + '--' + task['operator'] + '.json')


def main():
    if os.environ['SLURM_JOB_PARTITION'] != 'normal':
        raise RuntimeError('Approved normal allocation required')
    repo = Path(os.environ['RTC_REPO']).resolve()
    packet = repo / 'notes/e_resume_2026-11-02_v1/packet'
    manifest = packet / 'resume_code.sha256.json'
    if sha(manifest) != os.environ['RTC_E_RESUME_MANIFEST_SHA256']:
        raise RuntimeError('Recovery code seal differs')
    for rel, digest in read(manifest).items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts or sha(repo / rel) != digest:
            raise RuntimeError('Recovery source/input differs: ' + rel)
    selection = read(packet / 'selection.json')
    recovery = read(packet / 'resume_plan.json')
    chunk_index = int(os.environ['RTC_E_CHUNK'])
    chunk = recovery['chunks'][chunk_index]
    assert chunk['id'] == chunk_index
    assert recovery['fixture_all_passed'] and recovery['workers'] == 32
    assert recovery['wall_time'] == '03:00:00' and recovery['nodes_per_job'] == 1
    all_indices = [i for c in recovery['chunks'] for i in c['indices']]
    assert sorted(all_indices) == read(packet / 'retry_indices.json')
    assert len(all_indices) == len(set(all_indices)) == 9551
    assert not set(all_indices) & set(map(int, selection['completed_record_sha256']))
    assert sha(packet / 'selection.json') == recovery['selection_sha256']
    assert sha(packet / 'retry_indices.json') == recovery['retry_indices_sha256']
    bundle = repo / 'tacc_work/20261024-repair-v1/e-bundle'
    if sha(bundle / 'plan.json') != selection['source_plan_sha256']:
        raise RuntimeError('Original plan differs')
    plan = read(bundle / 'plan.json')
    old = bundle / 'study' / plan['output_relative']
    if read(old / 'STOP.json') != read(packet / 'quota_cause.json')['stop']:
        raise RuntimeError('Original infrastructure STOP differs')
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        if sha(old / name) != sha(packet / ('original-' + name)):
            raise RuntimeError('Original execution/task seal differs')
    execution = read(old / 'execution.json')
    tasks = read(old / 'tasks-evaluate.json')
    for rel, digest in plan['input_sha256'].items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Frozen input differs: ' + rel)
    for rel, digest in plan['code_sha256'].items():
        if sha(repo / rel) != digest:
            raise RuntimeError('Original scientific adapter differs: ' + rel)
    for vid, builds in execution['builds'].items():
        for operator, built in builds.items():
            if built['status'] == 'pass' and sha(bundle / 'study' / built['elf_path']) != built['elf_sha256']:
                raise RuntimeError('Original retained ELF differs: ' + vid + '/' + operator)
    if sha(Path(os.environ['RTC_IMAGE'])) != selection['image_sha256']:
        raise RuntimeError('Calibrated image differs')
    original_count = verify_originals(bundle, packet, selection)
    for index in chunk['indices']:
        task = tasks[index]
        assert task['index'] == index
        original = old / record_relative(task)
        if original.exists():
            try:
                read(original)
            except (ValueError, UnicodeError):
                pass
            else:
                raise RuntimeError('Selected index already has a finalized original: ' + str(index))
    # Preserve the calibrated 32-worker cap and the 80% memory rule.
    mem = {k: int(v.strip().split()[0]) for k, v in
           (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
           if k in ('MemTotal', 'MemAvailable')}
    available = mem['MemAvailable']
    for name in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        path = Path(name)
        if path.exists() and path.read_text().strip().isdigit():
            available = min(available, int(path.read_text().strip()) // 1024)
    # The fixture's complete profile observed at most 331924 KiB per worker.
    allowance = math.ceil(1.5 * 331924)
    if math.floor(.8 * available / allowance) < 32 or len(os.sched_getaffinity(0)) < 32:
        raise RuntimeError('Insufficient resources for frozen 32-worker schedule')
    output = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    output.relative_to(Path(os.environ['SCRATCH']).resolve())
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        with (output / name).open('xb') as dest:
            dest.write((old / name).read_bytes())
    for folder in ('builds', 'launcher', 'resources/evaluate', 'stdout/evaluate', 'processes/evaluate'):
        (output / folder).mkdir(parents=True, exist_ok=True)
    with (output / 'launcher/jobfile').open('x') as stream:
        for index in chunk['indices']:
            stream.write(shlex.join(['bash', '-l', str(repo / 'harness/tacc_e_resume/task_resume.sh'), str(index)]) + '\n')
    save(output / 'job_metadata/resume_setup.json', dict(
        chunk_id=chunk_index, indices=chunk['indices'], resume_plan_sha256=sha(packet / 'resume_plan.json'),
        code_manifest_sha256=sha(manifest), original_bundle=str(bundle),
        original_evidence_files_checked=original_count, original_stop_sha256=sha(old / 'STOP.json'),
        physical_output=str(output), logical_output='/study/' + plan['output_relative'],
        original_builds_read_only=True, original_metadata_read_only=True,
        original_finalized_records_retried=0, new_builds=0,
        available_memory_kib=available, per_worker_allowance_kib=allowance,
        workers=32, slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__ == '__main__':
    main()
