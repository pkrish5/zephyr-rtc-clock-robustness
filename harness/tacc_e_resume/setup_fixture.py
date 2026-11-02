#!/usr/bin/env python3
"""Read-only E recovery preflight and timing survey; never run firmware."""
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import statistics


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    if os.environ['SLURM_JOB_PARTITION'] != 'development':
        raise RuntimeError('Read-only fixture requires development')
    repo = Path(os.environ['RTC_REPO']).resolve()
    packet = repo / 'notes/e_resume_2026-11-02_v1/packet'
    selection = read(packet / 'selection.json')
    manifest_path = packet / 'fixture_code.sha256.json'
    if sha(manifest_path) != os.environ['RTC_E_FIXTURE_MANIFEST_SHA256']:
        raise RuntimeError('Fixture seal differs')
    for rel, digest in read(manifest_path).items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts or sha(repo / rel) != digest:
            raise RuntimeError('Fixture input differs: ' + rel)
    bundle = repo / 'tacc_work/20261024-repair-v1/e-bundle'
    plan = read(bundle / 'plan.json')
    if sha(bundle / 'plan.json') != selection['source_plan_sha256']:
        raise RuntimeError('Original plan differs')
    old = bundle / 'study' / plan['output_relative']
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        if sha(old / name) != sha(packet / ('original-' + name)):
            raise RuntimeError('Original execution metadata differs: ' + name)
    execution = read(old / 'execution.json')
    tasks = read(old / 'tasks-evaluate.json')
    retry = read(packet / 'retry_indices.json')
    assert len(tasks) == selection['total_indices'] == 17375
    assert len(retry) == selection['retry_count'] == 9551
    assert len(set(retry)) == len(retry)
    assert sha(packet / 'retry_indices.json') == selection['retry_indices_sha256']
    assert set(retry) == set(selection['incomplete_indices'] + selection['not_started_indices'])
    assert not (set(retry) & set(map(int, selection['completed_record_sha256'])))
    for rel, digest in plan['input_sha256'].items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Frozen input differs: ' + rel)
    for rel, digest in plan['code_sha256'].items():
        if sha(repo / rel) != digest:
            raise RuntimeError('Original evaluator source differs: ' + rel)
    for vid, builds in execution['builds'].items():
        for operator, built in builds.items():
            if built['status'] == 'pass' and sha(bundle / 'study' / built['elf_path']) != built['elf_sha256']:
                raise RuntimeError('Retained ELF differs: ' + vid + '/' + operator)
    if sha(Path(os.environ['RTC_IMAGE'])) != selection['image_sha256']:
        raise RuntimeError('Calibrated image differs')
    if sha(packet / 'old_verified_file_hashes.json') != selection['old_verified_files_sha256']:
        raise RuntimeError('Original-record hash ledger differs')
    verified = read(packet / 'old_verified_file_hashes.json')
    for rel, digest in verified.items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Completed old evidence differs: ' + rel)
    for index, files in selection['partial_files'].items():
        for rel, digest in files.items():
            if sha(bundle / rel) != digest:
                raise RuntimeError('Interrupted old evidence differs: ' + index)
    # A new completed original after the audit would invalidate the retry list.
    for index in retry:
        t = tasks[index]
        if t['index'] != index:
            raise RuntimeError('Task order differs')
        if t['operator'] == 'legal':
            rid = t['version_id'] + '-' + t['condition']
            if t['condition'] == 'seeded':
                rid += '-%03d' % t['seed']
            target = old / 'legal'
        else:
            rid = t['version_id'] + '--' + t['operator']
            target = old / 'faults'
        p = target / 'records' / (rid + '.json')
        if p.exists():
            # Even a newly finalized missing outcome must not be run again.
            try:
                read(p)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            else:
                raise RuntimeError('Retry index has a finalized original: ' + str(index))
    output = Path(os.environ['RTC_JOB_OUTPUT'])
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        (output / name).write_bytes((old / name).read_bytes())
    for folder in ('builds', 'launcher', 'fixture', 'resources/fixture', 'stdout/fixture'):
        (output / folder).mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    profiles = []
    for index_str in selection['completed_record_sha256']:
        index = int(index_str)
        p = old / 'resources/evaluate' / (str(index) + '.time')
        if not p.exists():
            profiles.append(dict(index=index, status='resource_file_missing'))
            continue
        text = p.read_text()
        elapsed = re.search(r'Elapsed \(wall clock\) time .*: ([\d:.]+)', text)
        peak = re.search(r'Maximum resident set size \(kbytes\): (\d+)', text)
        exit_status = re.search(r'Exit status: (\d+)', text)
        if not elapsed or not peak or not exit_status:
            profiles.append(dict(index=index, status='resource_file_incomplete', sha256=sha(p)))
            continue
        seconds = 0.
        for n in elapsed.group(1).split(':'):
            seconds = seconds * 60 + float(n)
        t = tasks[index]
        version = execution['versions'][t['version_id']]
        key = '|'.join((version['family'], version['variant'], t['operator']))
        groups[key].append(seconds)
        profiles.append(dict(index=index, status='resource_complete', seconds=seconds,
                             peak_rss_kib=int(peak.group(1)), exit_code=int(exit_status.group(1)),
                             group=key, sha256=sha(p)))

    def stats(values):
        values = sorted(values)
        return dict(count=len(values), median=statistics.median(values),
                    p95=values[math.ceil(.95 * len(values)) - 1], maximum=values[-1])

    values = [p['seconds'] for p in profiles if p['status'] == 'resource_complete']
    save(output / 'job_metadata/resource_profiles.json', profiles)
    save(output / 'job_metadata/resource_summary.json', dict(
        full_worker_elapsed_includes_replay_and_reference=True,
        profiles_complete=len(values), profiles_incomplete=len(profiles) - len(values),
        global_elapsed_seconds=stats(values),
        maximum_peak_rss_kib=max(p['peak_rss_kib'] for p in profiles if p['status'] == 'resource_complete'),
        groups={k: stats(v) for k, v in groups.items()}))
    # No Renode invocation: these tasks inspect the real intended container
    # mounts, source/ELF paths, runtime placement and copied sealed metadata.
    sample = [retry[(len(retry) - 1) * i // 31] for i in range(32)]
    with (output / 'launcher/jobfile').open('x') as stream:
        for index in sample:
            stream.write(shlex.join(['bash', '-l', str(repo / 'harness/tacc_e_resume/fixture_task.sh'), str(index)]) + '\n')
    save(output / 'job_metadata/fixture_setup.json', dict(
        fixture_code_manifest_sha256=sha(manifest_path),
        selection_sha256=sha(packet / 'selection.json'), checked_original_file_count=len(verified),
        original_metadata_sealed=True, retry_indices_checked=len(retry),
        protected_evaluations_preserved=selection['complete_and_valid'],
        fixture_indices=sample, new_simulations=0, new_builds=0,
        slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__ == '__main__':
    main()
