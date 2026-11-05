#!/usr/bin/env python3
"""Compute-only read audit; never invokes a test, build, or Renode."""
import hashlib
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write('\n')

def main():
    assert os.environ['SLURM_JOB_PARTITION'] == 'development'
    repo = Path(os.environ['RTC_REPO'])
    note = repo / 'notes/counter_repair_recovery_2026-11-05_v1'
    registration = json.loads((note / 'audit_plan.json').read_text())
    out = Path(os.environ['RTC_JOB_OUTPUT'])
    bundle = repo / registration['original_bundle_relative']
    plan_path = bundle / 'plan.json'
    assert sha(plan_path) == registration['original_plan_sha256']
    plan = json.loads(plan_path.read_text())
    old = bundle / plan['output_relative']
    seals = {}
    for relative, digest in registration['code_sha256'].items():
        assert sha(repo / relative) == digest, relative
    for relative, digest in registration['counter_inputs_sha256'].items():
        assert sha(repo / relative) == digest, relative
        seals['repo/' + relative] = digest
    for relative, digest in plan['input_sha256'].items():
        assert sha(bundle / relative) == digest, relative
        seals['bundle/' + relative] = digest
    for relative, digest in plan['code_sha256'].items():
        assert sha(repo / relative) == digest, relative
        seals['repo/' + relative] = digest
    image = repo / registration['image_relative']
    assert sha(image) == registration['image_sha256']
    paths = ['/opt/apps/lmod/lmod/init/sh', '/opt/apps/lmod/lmod/libexec/lmod']
    environment = dict(node=socket.getfqdn(), job_id=os.environ['SLURM_JOB_ID'],
                       apptainer_version=os.environ['RTC_APPTAINER_VERSION'],
                       loaded_modules=os.environ.get('LOADEDMODULES'),
                       module_paths={p: Path(p).is_file() for p in paths},
                       image_sha256=sha(image))
    assert all(environment['module_paths'].values())
    assert 'launcher/3.10' in os.environ['LOADEDMODULES'].split(':')
    probe = subprocess.run(['apptainer', 'exec', '--cleanenv', '--containall',
                            str(image), '/bin/true'], capture_output=True, text=True,
                           timeout=90)
    environment['container_true_probe'] = dict(exit_code=probe.returncode,
                                               stdout=probe.stdout, stderr=probe.stderr)
    save(out / 'environment.json', environment)
    assert probe.returncode == 0
    copies = []
    def keep(source):
        relative = source.relative_to(repo)
        target = out / 'evidence' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = sha(source)
        assert sha(target) == digest
        copies.append(dict(path=str(relative), sha256=digest))
    for p in [plan_path, bundle / 'plan.sha256', note / 'PROTOCOL.md', note / 'audit_plan.json']:
        keep(p)
    for relative in registration['counter_inputs_sha256']:
        keep(repo / relative)
    for p in (bundle / 'configs').glob('*'):
        if p.is_file(): keep(p)
    builds = []
    for unit in plan['units']:
        base = old / 'builds' / unit['id']
        record_path = base / 'build_record.json'
        record = json.loads(record_path.read_text())
        assert record['unit_id'] == unit['id'] and record['status'] == 'built'
        assert record['exit_code'] == 0 and record['error'] is None
        assert record['plan_sha256'] == sha(plan_path)
        assert record['container_sha256'] == registration['image_sha256']
        assert record['source_commit'] == plan['zephyr_commit']
        assert set(record['compiled_case_names']) == set(unit['expected_declared_cases'])
        assert sha(bundle / record['elf_path']) == record['elf_sha256']
        assert sha(base / 'build.log') == record['log_sha256']
        assert sha(bundle / unit['config']) == record['config_sha256']
        assert sha(bundle / unit['overlay']) == record['overlay_sha256']
        for p in [record_path, bundle / record['elf_path'], base / 'build.log']:
            keep(p)
        for relative, digest in record['build_products_sha256'].items():
            p = base / 'build' / relative
            assert sha(p) == digest
            keep(p)
        builds.append(dict(unit_id=unit['id'], elf_sha256=record['elf_sha256'],
                           build_record_sha256=sha(record_path), build_job=record['slurm_job_id']))
    primary = []
    for p in (old / 'records').glob('*.json'):
        record = json.loads(p.read_text())
        primary.append(dict(index=record['index'], sha256=sha(p)))
        keep(p)
    for folder in ['processes', 'resources', 'stdout', 'launcher']:
        for p in (old / folder).rglob('*'):
            if p.is_file(): keep(p)
    for p in (bundle.parent / 'slurm').glob('*'):
        if p.is_file(): keep(p)
    for name, digest in seals.items():
        location, relative = name.split('/', 1)
        assert sha((repo if location == 'repo' else bundle) / relative) == digest
    assert sha(plan_path) == registration['original_plan_sha256']
    save(out / 'audit.json', dict(builds=builds, existing_primary_records=primary,
                                 seals_unchanged=seals, copied_files=copies,
                                 scientific_tasks_executed=0, builds_executed=0,
                                 original_files_modified=0, original_jobs_changed=False))
    assert not primary, 'Unexpected existing primary outcomes; do not propose reruns'
    print(json.dumps(dict(verified_builds=len(builds), original_primary_records=0,
                          modules_and_container_probe_passed=True)))

if __name__ == '__main__':
    main()
