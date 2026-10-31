#!/usr/bin/env python3
"""Delete only approved regenerable state in the completed E/D build trees.

Final ELFs must match historical build records. All other ELFs, logs,
sources and metadata are sealed and retained. Original protected paths and
all input/hash records are excluded. Does not build or execute firmware.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')


def quota(work):
    return subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(work)],text=True)


def snapshot(repo,expected):
    present,absent={},[]
    for relative,digest in expected.items():
        path=repo/relative
        path.resolve().relative_to(repo)
        if path.exists():
            actual=sha(path)
            if actual!=digest:raise RuntimeError('Protected bytes differ; STOP: '+relative)
            present[relative]=actual
        else:absent.append(relative)
    return dict(present_sha256=present,absent=sorted(absent),changed=[])


def state_candidate(relative):
    """An allowlist inside build/, with conservative source/evidence exclusions."""
    p=Path(relative)
    if p.suffix.lower() in ('.elf','.c','.h','.cpp','.cc','.json','.yaml','.yml','.conf','.config','.dts','.overlay','.log','.sha256','.sha','.sha1','.sha512','.md5','.hash'):
        return False
    if 'checksum' in p.name.lower() or 'hash' in p.name.lower():return False
    if p.name in ('.config','build_record.json','build.log') or 'app' in p.parts:return False
    return (p.suffix.lower() in ('.o','.obj','.a','.pyc')
            or any(x in ('CMakeFiles','Kconfig','__pycache__') for x in p.parts)
            or p.name in ('CMakeCache.txt','build.ninja','.ninja_deps','.ninja_log','cmake_install.cmake'))


def identity(path):
    return dict(kind='symlink',target=os.readlink(path)) if path.is_symlink() else dict(kind='file',sha256=sha(path))


def main():
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development compute required')
    work=Path(os.environ['WORK']).resolve();repo=work/'zephyr-rtc-clock-robustness'
    out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();out.relative_to(Path(os.environ['SCRATCH']).resolve())
    out.mkdir(parents=True,exist_ok=False)
    boot=json.loads((repo/'tacc_work/20261029-quota-recovery-v1/bootstrap-3540791.json').read_text())
    if not boot['source_removed'] or boot['archive_sha256']!='1704dc2bc2f2b71f7d2fdb6c49319469704603a895defaaf3253f03585fd40ea':
        raise RuntimeError('A-B archive bootstrap must finish first')
    baseline=repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline)!='b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef':raise RuntimeError('Baseline differs')
    protected=json.loads(baseline.read_text())['hashes']
    before=snapshot(repo,protected);save(out/'protected_before.json',before)
    before_quota=quota(work)
    bundles=[repo/'tacc_work/20261024-repair-v1/e-bundle',repo/'tacc_work/20261024-d-cache-v2/d-cache-v2-bundle']
    keeps={};candidates={};verified_final_elfs=[];units=[];sealed_inputs=set()
    for bundle in bundles:
        plan=json.loads((bundle/'plan.json').read_text())
        if sha(bundle/'plan.json')!=(bundle/'plan.sha256').read_text().split()[0]:raise RuntimeError('Plan differs')
        for rel,digest in plan['input_sha256'].items():
            path=bundle/rel
            if sha(path)!=digest:raise RuntimeError('Frozen input differs: '+str(path))
            sealed_inputs.add(str(path))
        study=bundle/'study';result=study/plan['output_relative'];builds=result/'builds'
        metadata=list(builds.glob('*/*/build_record.json')) if plan['phase']=='E' else list((result/'build_records').glob('*.json'))
        if not metadata:raise RuntimeError('No authoritative build metadata: '+str(bundle))
        for record_path in metadata:
            record=json.loads(record_path.read_text())
            if record['status']!='pass':continue
            elf=study/record['elf_path']
            if sha(elf)!=record['elf_sha256']:raise RuntimeError('Recorded ELF differs: '+str(elf))
            keeps[str(elf)]=identity(elf);keeps[str(record_path)]=identity(record_path)
            verified_final_elfs.append(dict(path=str(elf),record=str(record_path),sha256=record['elf_sha256']))
            if record.get('log_path'):
                log=study/record['log_path']
                if sha(log)!=record['log_sha256']:raise RuntimeError('Build log differs: '+str(log))
                keeps[str(log)]=identity(log)
            for rel,digest in {**record.get('source_inputs',{}),**record.get('inputs',{})}.items():
                source=study/rel
                if sha(source)!=digest:raise RuntimeError('Recorded build input differs: '+str(source))
                sealed_inputs.add(str(source))
            if plan['phase']=='E':unit=record_path.parent
            else:
                # D records identify their actual unit through the logged ELF path.
                unit=elf.parent.parent.parent
                if unit.parent!=builds:raise RuntimeError('Unexpected D build-unit path: '+str(unit))
            target=unit/'build'
            if not target.is_dir():continue  # Reused original nominal ELF has no build tree.
            target.resolve().relative_to(builds.resolve())
            units.append(target)
            for current,dirs,files in os.walk(target,followlinks=False):
                leaves=list(files)+[d for d in dirs if (Path(current)/d).is_symlink()]
                for name in leaves:
                    path=Path(current)/name;relative=path.relative_to(target)
                    # os.walk does not follow directory links; the build root
                    # was resolved/contained above. Avoid a recursive lstat
                    # of every ancestor for every one of 500k build entries.
                    # Every ELF and log, and every non-allowlisted artifact, is retained.
                    if str(path) in sealed_inputs or not state_candidate(relative):
                        if path.is_file() or path.is_symlink():keeps[str(path)]=identity(path)
                        continue
                    protected_rel=str(path.relative_to(repo))
                    if protected_rel in protected or '20261026-git-checkout-recovery-v1' in str(path):
                        raise RuntimeError('Protected cleanup intersection; STOP: '+str(path))
                    if not path.is_symlink():
                        with path.open('rb') as stream:header=stream.read(20)
                        if header[:4]==b'\x7fELF':
                            endian='little' if header[5]==1 else 'big'
                            if int.from_bytes(header[16:18],endian) in (2,3):
                                keeps[str(path)]=identity(path)
                                continue  # Preserve linked ELF even without .elf suffix.
                    if path.is_symlink() or path.is_file():candidates[str(path)]=identity(path)
                    else:raise RuntimeError('Unexpected intermediate file type: '+str(path))
    # A recorded input found later must also veto an earlier candidate.
    if set(candidates)&(set(keeps)|sealed_inputs):raise RuntimeError('Keep/input collision; no deletion')
    save(out/'kept_file_hashes.json',keeps)
    save(out/'recorded_final_elfs.json',verified_final_elfs)
    save(out/'intermediate_deletion_manifest.json',candidates)
    print(json.dumps(dict(final_elf_records_verified=len(verified_final_elfs),kept_files=len(keeps),
                         approved_intermediates=len(candidates))),flush=True)
    for name,expected in keeps.items():
        if identity(Path(name))!=expected:raise RuntimeError('Kept file changed before cleanup: '+name)
    for name,expected in candidates.items():
        if identity(Path(name))!=expected:raise RuntimeError('Intermediate changed before cleanup: '+name)
    for name in candidates:Path(name).unlink()
    directories_removed=0
    for target in units:
        for current,dirs,files in os.walk(target,topdown=False,followlinks=False):
            p=Path(current)
            if p==target:continue
            try:p.rmdir();directories_removed+=1
            except OSError:pass  # Nonempty kept directories stay in place.
    for name,expected in keeps.items():
        if identity(Path(name))!=expected:raise RuntimeError('Kept bytes changed after cleanup: '+name)
    after=snapshot(repo,protected)
    if after!=before:raise RuntimeError('Protected presence/hash changed; STOP')
    save(out/'protected_after.json',after)
    receipt=dict(job_id=os.environ['SLURM_JOB_ID'],node=os.environ.get('SLURMD_NODENAME'),
        intermediates_removed=len(candidates),empty_intermediate_directories_removed=directories_removed,
        final_elf_records_verified=len(verified_final_elfs),kept_files_verified_unchanged=len(keeps),
        additional_elfs_and_logs_sealed_before_cleanup=True,
        protected_files_deleted=0,raw_verdict_records_deleted=0,frozen_sources_deleted=0,
        recovery_backup_deleted=False,new_builds=0,new_simulations=0,
        quota_before=before_quota,quota_after=quota(work),source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(out/'receipt.json',receipt)
    proof=out/'build-cleanup-proof.tar.gz'
    with proof.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as tar:
            for p in sorted(out.glob('*.json')):tar.add(p,arcname=p.name)
    dest=repo/'tacc_work/20261029-quota-recovery-v1';dest.mkdir(exist_ok=True)
    final=dest/('build-cleanup-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
    with proof.open('rb') as source,final.open('xb') as target:
        import shutil
        shutil.copyfileobj(source,target)
    if sha(final)!=sha(proof):raise RuntimeError('WORK proof differs')
    with final.with_suffix(final.suffix+'.sha256').open('x') as stream:stream.write(sha(final)+'  '+final.name+'\n')
    receipt.update(proof_archive=str(final),proof_sha256=sha(final),quota_final=quota(work))
    save(out/'final.json',receipt)
    with (dest/('build-cleanup-'+os.environ['SLURM_JOB_ID']+'.json')).open('x') as stream:
        json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
