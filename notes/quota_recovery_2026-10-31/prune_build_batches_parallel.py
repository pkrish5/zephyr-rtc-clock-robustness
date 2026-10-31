#!/usr/bin/env python3
"""Checkpointed infrastructure-only build cleanup, bounded below 30 minutes.

Keep all ELF executables, sources, logs and metadata. Verify final ELFs and
logs against build records. Intermediates use a stat/link identity manifest;
hashing their disposable contents is unnecessary. Scientific inputs and all
retained regular files are verified by SHA-256 before and after cleanup.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')


def snapshot(repo, hashes):
    def check(item):
        rel,digest=item
        if sha(repo/rel)!=digest:raise RuntimeError('Protected file differs: '+rel)
        return rel,digest
    values={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for n,(rel,digest) in enumerate(pool.map(check,hashes.items()),1):
            values[rel]=digest
            if n%1000==0:print('Protected audit',n,'/',len(hashes),flush=True)
    return values


def candidate(p):
    if p.suffix.lower() in ('.elf','.c','.h','.cpp','.cc','.cxx','.hpp','.hh','.hxx','.s','.asm','.py','.sh','.rs','.json','.yaml','.yml','.conf','.config','.dts','.overlay','.log','.sha256','.sha','.sha1','.sha512','.md5','.hash'):return False
    if 'checksum' in p.name.lower() or 'hash' in p.name.lower():return False
    if p.name in ('.config','build_record.json','build.log') or 'app' in p.parts:return False
    return (p.suffix.lower() in ('.o','.obj','.a','.pyc')
            or any(x in ('CMakeFiles','Kconfig','__pycache__') for x in p.parts)
            or p.name in ('CMakeCache.txt','build.ninja','.ninja_deps','.ninja_log','cmake_install.cmake'))


def disposable_identity(p):
    s=p.lstat()
    if stat.S_ISLNK(s.st_mode):return dict(kind='symlink',target=os.readlink(p))
    if not stat.S_ISREG(s.st_mode):raise RuntimeError('Unexpected intermediate type: '+str(p))
    return dict(kind='file',inode=s.st_ino,device=s.st_dev,size=s.st_size,mtime_ns=s.st_mtime_ns,mode=s.st_mode)


def retained_identity(p):
    return dict(kind='symlink',target=os.readlink(p)) if p.is_symlink() else dict(kind='file',sha256=sha(p))


def main():
    started=time.monotonic()
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development required')
    work=Path(os.environ['WORK']).resolve();repo=work/'zephyr-rtc-clock-robustness'
    out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();out.relative_to(Path(os.environ['SCRATCH']).resolve())
    out.mkdir(parents=True,exist_ok=False)
    recovery=repo/'tacc_work/20261029-quota-recovery-v1'
    baseline=repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline)!='b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef':raise RuntimeError('Baseline differs')
    protected=json.loads(baseline.read_text())['hashes']
    save(out/'protected_before.json',snapshot(repo,protected))
    print('All 30,067 protected hashes verified before cleanup.',flush=True)
    quota_before=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(work)],text=True)
    completed=set()
    for receipt in sorted(recovery.glob('build-batch-*.json')):
        r=json.loads(receipt.read_text())
        if not r['protected_after_verified'] or sha(Path(r['proof_archive']))!=r['proof_sha256']:
            raise RuntimeError('Prior batch is not verified: '+str(receipt))
        completed.update(row['build_record_path'] for row in r['completed_units'])
    units=[];inputs={};plans={}
    for name in ('20261024-repair-v1/e-bundle','20261024-d-cache-v2/d-cache-v2-bundle'):
        bundle=repo/'tacc_work'/name
        p=bundle/'plan.json';plan=json.loads(p.read_text())
        if sha(p)!=(bundle/'plan.sha256').read_text().split()[0]:raise RuntimeError('Plan differs')
        plans[str(p)]=sha(p)
        for rel,digest in plan['input_sha256'].items():inputs[str(bundle/rel)]=digest
        study=bundle/'study';result=study/plan['output_relative'];builds=result/'builds'
        records=sorted(builds.glob('*/*/build_record.json')) if plan['phase']=='E' else sorted((result/'build_records').glob('*.json'))
        if not records:raise RuntimeError('No build records: '+name)
        for record_path in records:
            if str(record_path) not in completed:units.append((record_path,study,builds,plan['phase']))
    for name,digest in inputs.items():
        if sha(Path(name))!=digest:raise RuntimeError('Frozen input differs: '+name)
    print('Frozen bundle inputs verified; pending build records:',len(units),flush=True)
    save(out/'frozen_input_hashes_before.json',inputs)
    done=[];removed=0;empty_dirs=0;kept_count=0
    # Bound the *whole* processing pass, including preflight, to 15 minutes.
    # Leave half the allocation for a final protected/input audit and packing.
    for record_path,study,builds,phase in units:
        if len(done)>=128 or time.monotonic()-started>=900:break
        print('Inspecting',record_path,flush=True)
        record=json.loads(record_path.read_text())
        if record['status']!='pass':
            done.append(dict(build_record_path=str(record_path),status='retained_failed_build',intermediates_removed=0))
            continue
        elf=study/record['elf_path']
        if sha(elf)!=record['elf_sha256']:raise RuntimeError('Recorded ELF differs: '+str(elf))
        keeps={str(elf):retained_identity(elf),str(record_path):retained_identity(record_path)}
        if record.get('log_path'):
            log=study/record['log_path']
            if sha(log)!=record['log_sha256']:raise RuntimeError('Build log differs: '+str(log))
            keeps[str(log)]=retained_identity(log)
        for rel,digest in {**record.get('source_inputs',{}),**record.get('inputs',{})}.items():
            p=study/rel
            if sha(p)!=digest:raise RuntimeError('Recorded source differs: '+str(p))
            keeps[str(p)]=retained_identity(p)
        unit=record_path.parent if phase=='E' else elf.parent.parent.parent
        if phase!='E' and unit.parent!=builds:raise RuntimeError('Unexpected D unit')
        target=unit/'build';leaves={};directories=[]
        if target.exists():
            target.resolve().relative_to(builds.resolve())
            if target.is_symlink():raise RuntimeError('Linked build root')
            stack=[target]
            while stack:
                current=stack.pop();directories.append(current)
                with os.scandir(current) as entries:
                    for entry in entries:
                        path=Path(entry.path)
                        if entry.is_dir(follow_symlinks=False):stack.append(path);continue
                        if not (entry.is_symlink() or entry.is_file(follow_symlinks=False)):
                            raise RuntimeError('Unexpected build entry type')
                        rel=path.relative_to(target)
                        if str(path) in inputs or str(path) in keeps or not candidate(rel):
                            keeps[str(path)]=retained_identity(path);continue
                        if str(path.relative_to(repo)) in protected or '20261026-git-checkout-recovery-v1' in str(path):
                            raise RuntimeError('Protected deletion intersection; STOP')
                        if not entry.is_symlink():
                            with path.open('rb') as f:header=f.read(20)
                            if header[:4]==b'\x7fELF':
                                if len(header)<20:raise RuntimeError('Truncated ELF header')
                                endian='little' if header[5]==1 else 'big'
                                if int.from_bytes(header[16:18],endian) in (2,3):
                                    keeps[str(path)]=retained_identity(path);continue
                        leaves[str(path)]=disposable_identity(path)
        if set(leaves)&(set(keeps)|set(inputs)):raise RuntimeError('Kept/input collision')
        index=len(done)
        manifest=dict(build_record=str(record_path),recorded_final_elf=str(elf),recorded_elf_sha256=record['elf_sha256'],
            retained_sha256_and_links=keeps,disposable_stat_and_links=leaves,
            protected_intersections=[],raw_verdict_intersections=[],recovery_backup_excluded=True)
        save(out/f'unit-{index:03d}-before.json',manifest)
        for name,identity in keeps.items():
            if retained_identity(Path(name))!=identity:raise RuntimeError('Kept file changed before deletion')
        for name,identity in leaves.items():
            if disposable_identity(Path(name))!=identity:raise RuntimeError('Intermediate changed before deletion')
        for name in leaves:Path(name).unlink()
        for directory in reversed(directories):
            if directory==target:continue
            try:directory.rmdir();empty_dirs+=1
            except OSError:pass
        for name,identity in keeps.items():
            if retained_identity(Path(name))!=identity:raise RuntimeError('Kept file changed after deletion')
        row=dict(build_record_path=str(record_path),status='verified',intermediates_removed=len(leaves),
            kept_files_verified=len(keeps),elf_sha256=record['elf_sha256'])
        save(out/f'unit-{index:03d}-after.json',row)
        done.append(row);removed+=len(leaves);kept_count+=len(keeps)
        print('Checkpoint:',len(done),'units,',removed,'regenerable leaves removed.',flush=True)
    for name,digest in {**inputs,**plans}.items():
        if sha(Path(name))!=digest:raise RuntimeError('Frozen bundle input/plan changed after cleanup')
    save(out/'protected_after.json',snapshot(repo,protected))
    receipt=dict(job_id=os.environ['SLURM_JOB_ID'],node=os.environ.get('SLURMD_NODENAME'),
        completed_units=done,remaining_build_records=len(units)-len(done),
        intermediates_removed=removed,empty_intermediate_directories_removed=empty_dirs,
        retained_file_checks=kept_count,protected_after_verified=True,protected_count=30067,
        protected_files_deleted=0,raw_verdict_records_deleted=0,frozen_sources_deleted=0,
        recovery_backup_deleted=False,new_builds=0,new_simulations=0,
        quota_before=quota_before,quota_after=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(work)],text=True),
        elapsed_seconds=round(time.monotonic()-started,1),source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(out/'receipt.json',receipt)
    proof=out/'build-batch-proof.tar.gz'
    with proof.open('xb') as f:
        with tarfile.open(fileobj=f,mode='w:gz') as tar:
            for p in sorted(out.glob('*.json')):tar.add(p,arcname=p.name)
    final=recovery/('build-batch-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
    with proof.open('rb') as source,final.open('xb') as target:shutil.copyfileobj(source,target)
    if sha(final)!=sha(proof):raise RuntimeError('WORK proof copy differs')
    with final.with_suffix(final.suffix+'.sha256').open('x') as f:f.write(sha(final)+'  '+final.name+'\n')
    receipt.update(proof_archive=str(final),proof_sha256=sha(final))
    save(out/'final.json',receipt);save(recovery/('build-batch-'+os.environ['SLURM_JOB_ID']+'.json'),receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
