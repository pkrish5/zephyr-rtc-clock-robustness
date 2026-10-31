#!/usr/bin/env python3
"""Verify and safely extract the returned primary archive; repeat the audit.

Runs only local analysis of copied evidence. Never runs a test or writes to
the original LS6 results. Archive paths, links and manifest completeness are
checked before trusting any returned report.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

from audit_primary import save, sha


def safe_relative(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:
        raise RuntimeError('Unsafe archive/manifest path: ' + name)
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'checksum', 'dest', 'repo', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    digest = sha(args.archive)
    if digest != args.checksum.read_text().split()[0]:
        raise RuntimeError('Archive checksum differs')
    args.dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(args.archive, 'r:gz') as tar:
        members = tar.getmembers()
        names = set()
        roots = set()
        for m in members:
            path = safe_relative(m.name)
            if not path.parts or str(path) in names or not (m.isdir() or m.isfile()):
                raise RuntimeError('Unexpected archive member: ' + m.name)
            names.add(str(path))
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise RuntimeError('Expected one top-level evidence directory')
        for m in members:
            target = args.dest / m.name
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as source, target.open('xb') as stream:
                    shutil.copyfileobj(source, stream)
    evidence = args.dest / next(iter(roots))
    manifest = json.loads((evidence / 'files.sha256.json').read_text())
    actual = {str(p.relative_to(evidence)) for p in evidence.rglob('*') if p.is_file()}
    if actual != set(manifest) | {'files.sha256.json'}:
        raise RuntimeError('Manifest does not cover the extracted file set')
    for relative, expected in manifest.items():
        safe_relative(relative)
        if sha(evidence / relative) != expected:
            raise RuntimeError('Extracted file checksum differs: ' + relative)
    source_manifest = json.loads((evidence / 'snapshot_source_sha256.json').read_text())
    for relative, expected in source_manifest.items():
        if manifest.get(relative) != expected:
            raise RuntimeError('Source/copy hash mismatch: ' + relative)
    protection = {}
    for name in ('protected_before.json', 'protected_after.json'):
        report = json.loads((evidence / name).read_text())
        if report['count'] != 30067 or report['changed']:
            raise RuntimeError('Protected-file audit failed: ' + name)
        protection[name] = sha(evidence / name)
    collector = json.loads((evidence / 'collector.json').read_text())
    if collector['new_simulations'] != 0 or collector['new_builds'] != 0:
        raise RuntimeError('Unexpected execution in collector')
    subprocess.run([sys.executable, str(Path(__file__).with_name('audit_primary.py')),
                    '--bundle', str(evidence / 'bundle'),
                    '--sealed-plan', str(args.repo / 'results/s2_production_20261026_v1/plan.json'),
                    '--nominal-cases', str(evidence / 'nominal_cases.csv'),
                    '--repo', str(args.repo), '--out', str(args.out)], check=True)
    agreed = []
    for remote in sorted((evidence / 'audit').iterdir()):
        if remote.is_file():
            local = args.out / remote.name
            if sha(remote) != sha(local):
                raise RuntimeError('Independent local audit differs: ' + remote.name)
            agreed.append(remote.name)
    save(args.out / 'return_verification.json', dict(archive_sha256=digest,
        archive_bytes=args.archive.stat().st_size, manifest_files_verified=len(manifest),
        source_snapshot_files_verified=len(source_manifest),
        independent_audit_files_matching=agreed, protected_audits=protection,
        collector=collector, new_simulations=0, new_builds=0,
        replay_reference_attribution_complete=False))
    print(json.dumps(dict(archive_sha256=digest, files_verified=len(manifest),
        independent_audit_files_matching=agreed)))


if __name__ == '__main__':
    main()
