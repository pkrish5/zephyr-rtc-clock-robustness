#!/usr/bin/env python3
"""Inspect read-only originals and write only a new synthetic fixture receipt."""
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def readonly(path):
    assert os.statvfs(path).f_flag & os.ST_RDONLY, str(path)


index = int(sys.argv[1])
assert os.environ['SLURM_JOB_PARTITION'] == 'development'
packet = Path('/recovery-packet')
selection = read(packet / 'selection.json')
assert index in read(packet / 'retry_indices.json')
old_plan = Path('/bundle/plan.json')
assert sha(old_plan) == selection['source_plan_sha256']
plan = read(old_plan)
out = Path('/study') / plan['output_relative']
other = Path('/bundle/study') / plan['output_relative']
original = Path('/original/study') / plan['output_relative']
assert (original / 'STOP.json').is_file()
assert not (out / 'STOP.json').exists()
for root in (out, other):
    for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
        assert sha(root / name) == sha(packet / ('original-' + name))
        readonly(root / name)
    readonly(root / 'builds')
    assert not os.statvfs(root / 'fixture').f_flag & os.ST_RDONLY
readonly(Path('/original'))
readonly(old_plan)
readonly(Path('/phase2'))
execution = read(out / 'execution.json')
task = read(out / 'tasks-evaluate.json')[index]
assert task['index'] == index
vid = task['version_id']
for op, built in execution['builds'][vid].items():
    if built['status'] == 'pass':
        for study in (Path('/study'), Path('/bundle/study')):
            elf = study / built['elf_path']
            readonly(elf)
            assert sha(elf) == built['elf_sha256']
for rel, digest in plan['code_sha256'].items():
    assert sha(Path('/phase2') / Path(rel).name) == digest
for rel, digest in plan['frozen_code_sha256'].items():
    assert sha(Path('/opt/rtc-code') / rel) == digest
for p in (Path('/home/rtc'), Path('/tmp'), Path('/var/tmp')):
    assert not os.statvfs(p).f_flag & os.ST_RDONLY
assert os.environ['XDG_CACHE_HOME'] == '/var/tmp'
with (out / 'fixture' / ('%05d.json' % index)).open('x') as stream:
    json.dump(dict(index=index, all_mount_checks_passed=True,
                   original_stop_preserved=True, sealed_metadata_read_only=True,
                   retained_elf_hashes_match=True, frozen_code_hashes_match=True,
                   new_simulations=0, new_builds=0,
                   slurm_job_id=os.environ['SLURM_JOB_ID']), stream, indent=2)
    stream.write('\n')
