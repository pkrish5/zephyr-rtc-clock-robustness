#!/usr/bin/env python3
"""Provision missing, byte-identical audit dependencies on development.

This does not change the collector, the archive selection, or existing
protected files. The cache contains original ignored build artifacts; no
artifact is rebuilt. Existing paths must already match the original ledger.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

BASELINE_SHA256 = 'b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def target_path(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative:
        raise RuntimeError('Unsafe audit path: ' + relative)
    if not path.parts or path.parts[0] in ('.git', '.ssh', '.aws', '.codex', '.agents'):
        raise RuntimeError('Disallowed audit path: ' + relative)
    target = root / relative
    target.resolve().relative_to(root)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'cache', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('SLURM_JOB_PARTITION') != 'development':
        raise RuntimeError('Audit path provisioning requires development compute')
    root = args.repo.resolve()
    root.relative_to(Path(os.environ['WORK']).resolve())
    args.cache.resolve().relative_to(root)
    args.out.resolve().relative_to(root)
    if args.out.exists():
        raise RuntimeError('Preserve prior staging receipt; choose a new output')
    baseline = args.cache / 'baseline.json'
    if sha(baseline) != BASELINE_SHA256:
        raise RuntimeError('Original baseline bytes differ')
    ledger = json.loads(baseline.read_text())
    expected = ledger['hashes']
    if ledger['protected_count'] != 30067 or len(expected) != 30067:
        raise RuntimeError('Original protected set differs')
    manifest = json.loads((args.cache / 'cache_manifest.json').read_text())
    archive = args.cache / 'protected_files.tar.gz'
    if sha(archive) != manifest['archive_sha256']:
        raise RuntimeError('Audit dependency cache differs')
    if manifest['baseline_sha256'] != BASELINE_SHA256:
        raise RuntimeError('Cache baseline identity differs')
    cached = manifest['files']
    for relative, info in cached.items():
        target_path(root, relative)
        if expected.get(relative) != info['sha256']:
            raise RuntimeError('Cache is not an original protected file: ' + relative)
    missing = []
    present = {}
    # All existing protected bytes are checked before any missing path is filled.
    for relative, digest in expected.items():
        target = target_path(root, relative)
        if target.exists():
            if not target.is_file() or sha(target) != digest:
                raise RuntimeError('Existing protected file differs; do not overwrite: ' + relative)
            present[relative] = digest
        else:
            if target.is_symlink() or relative not in cached:
                raise RuntimeError('Missing protected path is not safely cached: ' + relative)
            missing.append(relative)
    canonical = root / 'artifacts/tacc_phase2_20261024_v1/protected_baseline.json'
    if canonical.exists() and sha(canonical) != BASELINE_SHA256:
        raise RuntimeError('Existing baseline differs; do not overwrite')
    # Verify every cached member before creating a protected file.
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        if len(members) != len(cached) or {m.name for m in members} != set(cached):
            raise RuntimeError('Audit cache member set differs')
        for member in members:
            target_path(root, member.name)
            if not member.isfile() or member.size != cached[member.name]['size_bytes']:
                raise RuntimeError('Unexpected cache member: ' + member.name)
            with tar.extractfile(member) as stream:
                digest = hashlib.sha256(stream.read()).hexdigest()
            if digest != expected[member.name]:
                raise RuntimeError('Cached original bytes differ: ' + member.name)
    with tarfile.open(archive, 'r:gz') as tar:
        for relative in missing:
            target = target_path(root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(relative) as source, target.open('xb') as stream:
                shutil.copyfileobj(source, stream)
            if sha(target) != expected[relative]:
                raise RuntimeError('Provisioned bytes differ: ' + relative)
    if not canonical.exists():
        canonical.parent.mkdir(parents=True, exist_ok=True)
        with baseline.open('rb') as source, canonical.open('xb') as stream:
            shutil.copyfileobj(source, stream)
    for relative, digest in present.items():
        if sha(target_path(root, relative)) != digest:
            raise RuntimeError('Pre-existing protected file changed: ' + relative)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    protected_report = args.out.with_suffix('.protected.json')
    subprocess.run([sys.executable, str(root / 'harness/tacc_phase2/audit.py'),
                    'check', '--root', str(root), '--snapshot', str(canonical),
                    '--out', str(protected_report)], check=True)
    with args.out.open('x') as stream:
        json.dump(dict(slurm_job_id=os.environ['SLURM_JOB_ID'],
            baseline_sha256=BASELINE_SHA256, original_protected_count=30067,
            existing_files_verified_unchanged=len(present),
            missing_paths_provisioned={p: expected[p] for p in missing},
            pre_existing_files_overwritten=0,
            protected_audit_sha256=sha(protected_report),
            cache_sha256=sha(archive), new_builds=0, new_simulations=0,
            archive_collector_changed=False, archive_selection_changed=False),
            stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(existing_unchanged=len(present), original_copies_provisioned=len(missing),
                         protected_files_verified=30067, receipt=str(args.out))))


if __name__ == '__main__':
    main()
