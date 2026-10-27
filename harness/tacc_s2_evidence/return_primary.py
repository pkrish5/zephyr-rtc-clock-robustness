#!/usr/bin/env python3
"""Snapshot/audit/archive finished S2 primary evidence on a compute node.

No builds, simulation, replay, or source changes. Creates a new destination;
the original records are read only. One archive avoids a recursive rsync of
thousands of WORK files. Runtime home/cache directories are not included.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

from audit_primary import save, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'bundle', 'dest', 'slurm-logs', 'image'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('SLURM_JOB_PARTITION') != 'development':
        raise RuntimeError('Read-only evidence collection requires a development compute job')
    repo = args.repo.resolve()
    work = Path(os.environ['WORK']).resolve()
    repo.relative_to(work)
    for path in (args.bundle, args.dest, args.slurm_logs, args.image):
        path.resolve().relative_to(repo)
    plan = json.loads((args.bundle / 'plan.json').read_text())
    if sha(args.bundle / 'plan.json') != (args.bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Plan seal differs')
    if sha(args.image) != plan['image_sha256']:
        raise RuntimeError('Container hash differs')
    args.dest.mkdir(parents=True, exist_ok=False)
    baseline = repo / 'artifacts/tacc_phase2_20261024_v1/protected_baseline.json'
    audit = repo / 'harness/tacc_phase2/audit.py'
    subprocess.run([sys.executable, str(audit), 'check', '--root', str(repo),
                    '--snapshot', str(baseline), '--out', str(args.dest / 'protected_before.json')], check=True)

    source_hashes = {}
    for source, label in ((args.bundle, 'bundle'), (args.slurm_logs, 'slurm')):
        for path in sorted(source.rglob('*')):
            if path.is_symlink():
                raise RuntimeError('Unexpected symlink in evidence: ' + str(path))
            if not path.is_file():
                continue
            relative = Path(label) / path.relative_to(source)
            target = args.dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            before = sha(path)
            shutil.copyfile(path, target)
            if sha(target) != before or sha(path) != before:
                raise RuntimeError('Evidence changed during snapshot: ' + str(path))
            source_hashes[str(relative)] = before
    code = args.dest / 'code'
    for rel, digest in plan['code_sha256'].items():
        path = repo / rel
        if sha(path) != digest:
            raise RuntimeError('Frozen execution code differs: ' + rel)
        target = code / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name in ('audit_primary.py', 'return_primary.py', 'return_primary.sbatch'):
        target = code / 'harness/tacc_s2_evidence' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / 'harness/tacc_s2_evidence' / name, target)
    if sha(repo / 'paper/DESIGN.md') != plan['design_sha256']:
        raise RuntimeError('Registered design differs')
    shutil.copyfile(repo / 'paper/DESIGN.md', args.dest / 'DESIGN.md')
    nominal = repo / 'analysis/s2_qualification_final_20261026_v1/per_case_cohort.csv'
    shutil.copyfile(nominal, args.dest / 'nominal_cases.csv')
    subprocess.run([sys.executable, str(Path(__file__).with_name('audit_primary.py')),
                    '--bundle', str(args.dest / 'bundle'), '--sealed-plan', str(args.bundle / 'plan.json'),
                    '--nominal-cases', str(nominal), '--repo', str(repo),
                    '--out', str(args.dest / 'audit')], check=True)
    subprocess.run([sys.executable, str(audit), 'check', '--root', str(repo),
                    '--snapshot', str(baseline), '--out', str(args.dest / 'protected_after.json')], check=True)
    save(args.dest / 'snapshot_source_sha256.json', source_hashes)
    save(args.dest / 'collector.json', dict(job_id=os.environ['SLURM_JOB_ID'],
        partition=os.environ['SLURM_JOB_PARTITION'], node=os.environ.get('SLURMD_NODENAME'),
        plan_sha256=sha(args.bundle / 'plan.json'), container_sha256=sha(args.image),
        apptainer_version=os.environ['RTC_APPTAINER_VERSION'],
        new_builds=0, new_simulations=0, runtime_cache_included=False,
        primary_job_id='3535524', E2_started=False, manuscript_edited=False))
    manifest = {str(p.relative_to(args.dest)): sha(p)
                for p in sorted(args.dest.rglob('*')) if p.is_file()}
    save(args.dest / 'files.sha256.json', manifest)
    archive = args.dest.with_suffix('.tar.gz')
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w:gz') as tar:
            tar.add(args.dest, arcname=args.dest.name)
    with archive.with_suffix(archive.suffix + '.sha256').open('x') as stream:
        stream.write(sha(archive) + '  ' + archive.name + '\n')
    print(json.dumps(dict(archive=str(archive), sha256=sha(archive), files=len(manifest))))


if __name__ == '__main__':
    main()
