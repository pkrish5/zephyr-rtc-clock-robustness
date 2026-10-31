#!/usr/bin/env python3
"""Reverify the existing complete A-B archive, then prune only its loose output.

Requires development compute, a known archive retained on WORK, exact tar
coverage/content equivalence, no protected/input/ELF/source intersection,
and unchanged original protected bytes. No test runs or rebuilds.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile

EXPECTED_ARCHIVE = '1704dc2bc2f2b71f7d2fdb6c49319469704603a895defaaf3253f03585fd40ea'
BASELINE = 'b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def quota(work):
    result = subprocess.run(['lfs', 'quota', '-u', os.environ['USER'], str(work)],
                            capture_output=True, text=True, check=True)
    return result.stdout


def protected_snapshot(repo, expected):
    present, absent = {}, []
    for relative, digest in expected.items():
        path = repo / relative
        path.resolve().relative_to(repo)
        if path.exists():
            actual = sha(path)
            if actual != digest:
                raise RuntimeError('Protected file differs; STOP: ' + relative)
            present[relative] = actual
        else:
            if path.is_symlink():
                raise RuntimeError('Broken protected link; STOP: ' + relative)
            absent.append(relative)
    return dict(protected_count=len(expected), present_sha256=present,
                absent_before_cleanup=sorted(absent), changed=[])


def inventory(source):
    result = {source.name: dict(kind='directory')}
    stack = [source]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                name = str(path.relative_to(source.parent))
                if entry.is_symlink():
                    raise RuntimeError('Unexpected result symlink; no cleanup: ' + name)
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                    result[name] = dict(kind='directory')
                elif entry.is_file(follow_symlinks=False):
                    if path.suffix.lower() in ('.elf', '.c', '.h', '.cpp', '.cc') or path.name in ('build.log','build_record.json'):
                        raise RuntimeError('ELF/source/build evidence must remain loose; STOP: ' + name)
                    result[name] = dict(kind='file',sha256=sha(path),size=entry.stat(follow_symlinks=False).st_size)
                else:
                    raise RuntimeError('Unexpected result file type; no cleanup: ' + name)
    return result


def main():
    if os.environ.get('SLURM_JOB_PARTITION') != 'development':
        raise RuntimeError('Development compute only')
    work = Path(os.environ['WORK']).resolve()
    scratch = Path(os.environ['SCRATCH']).resolve()
    repo = work / 'zephyr-rtc-clock-robustness'
    out = Path(os.environ['RTC_RECOVERY_REPORT']).resolve()
    out.relative_to(scratch)
    out.mkdir(parents=True, exist_ok=False)
    source = repo / 'tacc_work/20261024-phase2/ab-bundle/study/results/tacc_phase2_ab_20261024_v1'
    bundle = repo / 'tacc_work/20261024-phase2/ab-bundle'
    archive = repo / 'tacc_work/20261024-return-v1/ab-results.tar.gz'
    source.resolve().relative_to(repo)
    if source.is_symlink() or not source.is_dir():
        raise RuntimeError('Expected original result directory absent or linked')
    baseline = repo / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline) != BASELINE:
        raise RuntimeError('Original baseline seal differs')
    expected = json.loads(baseline.read_text())['hashes']
    source_relative = str(source.relative_to(repo))
    if any(p == source_relative or p.startswith(source_relative + '/') for p in expected):
        raise RuntimeError('Protected deletion intersection; STOP after diagnosis')
    if '20261026-git-checkout-recovery-v1' in str(source):
        raise RuntimeError('Recovery backup is never a cleanup target')
    plan = json.loads((bundle / 'plan.json').read_text())
    if sha(bundle / 'plan.json') != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('A-B plan seal differs')
    if plan['phase'] != 'AB' or len(plan['tasks']) != 1632:
        raise RuntimeError('Unexpected completed application')
    for relative in plan['input_sha256']:
        p = bundle / relative
        try:
            p.resolve().relative_to(source)
        except ValueError:
            continue
        raise RuntimeError('Frozen bundle input in deletion target; STOP: ' + str(p))
    report = json.loads((source / 'report.json').read_text())
    if not report['complete'] or report['records'] != 1632 or report['outcomes'] != {'pass':1632} or report['stop_marker']:
        raise RuntimeError('Directory is not the previously completed A-B result')
    before_quota = quota(work)
    before = protected_snapshot(repo, expected)
    save(out / 'protected_before.json', before)
    if sha(archive) != EXPECTED_ARCHIVE:
        raise RuntimeError('Existing WORK archive differs')
    original = inventory(source)
    save(out / 'original_files.json', original)
    extraction = out / 'extracted'
    extraction.mkdir()
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        names = set()
        for member in members:
            p = PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or '\\' in member.name or member.name in names:
                raise RuntimeError('Unsafe or duplicate archive path')
            names.add(member.name)
            expected_row = original.get(member.name)
            if expected_row is None or not (member.isfile() or member.isdir()):
                raise RuntimeError('Archive member set/type differs')
            if member.isdir() != (expected_row['kind'] == 'directory'):
                raise RuntimeError('Archive member type differs')
        if names != set(original):
            raise RuntimeError('Archive does not list every current original entry')
        for member in members:
            target = extraction / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                if sha(target) != original[member.name]['sha256']:
                    raise RuntimeError('Extracted/original hash differs: ' + member.name)
    # Re-read every original immediately before the approved deletion.
    if inventory(source) != original or sha(archive) != EXPECTED_ARCHIVE:
        raise RuntimeError('Originals/archive changed during verification; no deletion')
    save(out / 'verified_before_deletion.json', dict(archive=str(archive),archive_sha256=EXPECTED_ARCHIVE,
        exact_entry_set=True,entries=len(original),files=sum(r['kind']=='file' for r in original.values()),
        extracted_hashes_match=True,protected_intersections=[],frozen_input_intersections=[],
        elf_source_build_log_intersections=[],recovery_backup_excluded=True,
        archive_retained_on_work=True,independent_mac_archive_preverified=True))
    print('Archive complete and extracted hashes match; pruning only the approved A-B loose output.',flush=True)
    shutil.rmtree(source)
    after = protected_snapshot(repo, expected)
    if after != before:
        raise RuntimeError('Protected file presence/hash changed; STOP')
    save(out / 'protected_after.json', after)
    receipt = dict(job_id=os.environ['SLURM_JOB_ID'],node=os.environ.get('SLURMD_NODENAME'),
        source=str(source),source_removed=not source.exists(),archive=str(archive),archive_sha256=sha(archive),
        verified_entries=len(original),regular_files_archived=sum(r['kind']=='file' for r in original.values()),
        protected_files_deleted=0,frozen_inputs_deleted=0,elfs_deleted=0,build_logs_deleted=0,
        recovery_backup_deleted=False,new_simulations=0,new_builds=0,
        existing_protected_files_unchanged=len(before['present_sha256']),
        pre_existing_absent_protected_paths=len(before['absent_before_cleanup']),
        quota_before=before_quota,quota_after_prune=quota(work),
        source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(out / 'receipt.json', receipt)
    proof = out / 'bootstrap-proof.tar.gz'
    with proof.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as tar:
            for p in sorted(out.glob('*.json')):
                tar.add(p,arcname=p.name)
    dest = repo / 'tacc_work/20261029-quota-recovery-v1'
    dest.mkdir(parents=True,exist_ok=True)
    target = dest / ('bootstrap-' + os.environ['SLURM_JOB_ID'] + '.tar.gz')
    with proof.open('rb') as src,target.open('xb') as dst:
        shutil.copyfileobj(src,dst)
    if sha(target) != sha(proof):
        raise RuntimeError('WORK proof archive copy differs')
    with target.with_suffix(target.suffix+'.sha256').open('x') as stream:
        stream.write(sha(target)+'  '+target.name+'\n')
    final_path = dest / ('bootstrap-' + os.environ['SLURM_JOB_ID'] + '.json')
    with final_path.open('x') as stream:
        final = dict(receipt,quota_final=quota(work),proof_archive=str(target),proof_sha256=sha(target))
        json.dump(final,stream,indent=2,sort_keys=True);stream.write('\n')
    save(out/'final.json',final)
    print(json.dumps(final,indent=2),flush=True)


if __name__=='__main__':
    main()
