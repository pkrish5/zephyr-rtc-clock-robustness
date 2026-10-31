#!/usr/bin/env python3
"""Archive and verify selected closed outputs before pruning disposable leaves.

No experiment execution. Configuration is appended to a fresh submitted
source after inventory review. Partial E and S2 production are excluded.
Protected files, sealed bundle inputs, builds, ELFs, sources, build logs and
recorded hash metadata remain loose. Archives and proofs remain on WORK.
"""
import hashlib
import gzip
import json
import os
from pathlib import Path, PurePosixPath
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


def inventory(root):
    result={'.':dict(kind='directory')};stack=[root]
    while stack:
        directory=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                p=Path(entry.path);rel=str(p.relative_to(root))
                if entry.is_symlink():result[rel]=dict(kind='symlink',target=os.readlink(p))
                elif entry.is_dir(follow_symlinks=False):result[rel]=dict(kind='directory');stack.append(p)
                elif entry.is_file(follow_symlinks=False):
                    s=entry.stat(follow_symlinks=False)
                    result[rel]=dict(kind='file',sha256=sha(p),size=s.st_size)
                else:raise RuntimeError('Special entry; preserve original: '+str(p))
    return result


def snapshot(repo,expected):
    def check(item):
        rel,digest=item
        if sha(repo/rel)!=digest:raise RuntimeError('Protected hash differs: '+rel)
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(check,expected.items()))
    return expected


def must_keep(repo,source,rel,protected,inputs,prune_generated=False,recorded_products=()):
    p=source/rel;parts=Path(rel).parts;name=p.name.lower()
    if str(p.relative_to(repo)) in protected or str(p) in inputs:return True
    if str(p) in recorded_products:return True
    if '20261026-git-checkout-recovery-v1' in str(p):return True
    generated_build=prune_generated and 'build' in parts
    if 'build_records' in parts:return True
    if any(x in ('builds','build','app') for x in parts) and not generated_build:return True
    if not generated_build and p.suffix.lower() in ('.c','.h','.cpp','.cc','.cxx','.hpp','.hh','.s','.asm','.sh','.py'):return True
    if p.suffix.lower() in ('.elf','.bin','.json','.yaml','.yml','.conf','.config','.dts','.overlay','.sha256','.sha','.sha1','.sha512','.md5','.hash') and generated_build:return True
    if p.suffix.lower() in ('.elf','.sha256','.sha','.sha1','.sha512','.md5','.hash'):return True
    if name.startswith('.config'):return True
    if p.parent==source and p.suffix.lower()=='.json':return True
    if 'build' in name and name.endswith('.log'):return True
    if any(x in name for x in ('forecast','manifest','checksum','lock','execution')):return True
    if p.is_file() and not p.is_symlink():
        with p.open('rb') as f:head=f.read(20)
        if head[:4]==b'\x7fELF':
            if not generated_build or p.suffix.lower() not in ('.o','.obj'):return True
            if len(head)<20:raise RuntimeError('Truncated object/ELF header')
            endian='little' if head[5]==1 else 'big'
            if int.from_bytes(head[16:18],endian) in (2,3):return True
    return False


def pack(source,original,archive):
    # Explicit TarInfo avoids following links or implicit hard-link aliases.
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz',compresslevel=1) as tar:
            for rel,row in sorted(original.items()):
                path=source if rel=='.' else source/rel
                name='output' if rel=='.' else 'output/'+rel
                s=path.lstat()
                info=tarfile.TarInfo(name);info.mode=stat.S_IMODE(s.st_mode)
                info.mtime=s.st_mtime;info.uid=s.st_uid;info.gid=s.st_gid
                if row['kind']=='directory':info.type=tarfile.DIRTYPE;tar.addfile(info)
                elif row['kind']=='symlink':
                    info.type=tarfile.SYMTYPE;info.linkname=row['target'];tar.addfile(info)
                else:
                    if path.is_symlink():raise RuntimeError('File type changed during packing')
                    info.size=row['size'];info.type=tarfile.REGTYPE
                    with path.open('rb') as f:tar.addfile(info,f)


def verify(archive,original):
    names=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='output':
                raise RuntimeError('Unsafe archive name')
            rel='.' if len(path.parts)==1 else str(PurePosixPath(*path.parts[1:]))
            if rel in names or rel not in original:raise RuntimeError('Duplicate/unexpected archive entry')
            names.add(rel);row=original[rel]
            if row['kind']=='directory':
                if not member.isdir():raise RuntimeError('Directory type differs')
            elif row['kind']=='symlink':
                if not member.issym() or member.linkname!=row['target']:raise RuntimeError('Symlink differs')
            else:
                if not member.isfile() or member.size!=row['size']:raise RuntimeError('File type/size differs')
                h=hashlib.sha256()
                with tar.extractfile(member) as f:
                    for b in iter(lambda:f.read(1048576),b''):h.update(b)
                if h.hexdigest()!=row['sha256']:raise RuntimeError('Extracted stream hash differs: '+rel)
    if names!=set(original):raise RuntimeError('Archive does not list every original entry')


def main(targets):
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Compute-only infrastructure job')
    repo=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
    scratch=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();scratch.relative_to(Path(os.environ['SCRATCH']).resolve())
    scratch.mkdir(parents=True,exist_ok=False)
    baseline=repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline)!='b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef':raise RuntimeError('Baseline differs')
    protected=json.loads(baseline.read_text())['hashes']
    save(scratch/'targets.json',targets)
    save(scratch/'protected_before.json',snapshot(repo,protected))
    # Only plans, not arbitrary result replicas, define immutable bundle input paths.
    inputs=set()
    for attempt in (repo/'tacc_work').iterdir():
        if not attempt.is_dir():continue
        for bundle in attempt.iterdir():
            if not bundle.is_dir() or 'bundle' not in bundle.name:continue
            for name in ('plan.json','calibration_plan.json'):
                p=bundle/name
                if p.exists():
                    plan=json.loads(p.read_text())
                    # Plan paths are already rooted in this absolute bundle.
                    # Do not follow a regenerated build link into a source tree.
                    for rel in plan.get('input_sha256',{}):
                        if Path(rel).is_absolute() or '..' in Path(rel).parts:raise RuntimeError('Unsafe sealed input path')
                        inputs.add(str(bundle/rel))
    final=repo/'tacc_work'/'20261031-verified-closed-outputs';final.mkdir(exist_ok=True)
    completed=[]
    for i,target in enumerate(targets):
        source=repo/target['relative_path'];source.resolve().relative_to(repo)
        text=str(source)
        if source.is_symlink() or '20261026-git-checkout-recovery-v1' in text:
            raise RuntimeError('Linked root or protected recovery backup')
        if any(x in text for x in ('tacc_phase2_e_20261024_v1','s2_production_20261026_v1')):
            raise RuntimeError('Partial E and priority S2 originals are excluded')
        if not source.is_dir():raise RuntimeError('Expected original absent')
        ev=repo/target['completion_evidence']
        if sha(ev)!=target['completion_evidence_sha256']:raise RuntimeError('Completion evidence changed')
        recorded_products=set()
        if target.get('prune_generated_build'):
            # This mode is restricted to the completed, validated D v2 arm.
            allowed='tacc_work/20261024-d-cache-v2/d-cache-v2-bundle/study/results/tacc_phase2_d_20261024_v2'
            if target['relative_path']!=allowed:raise RuntimeError('Generated-build pruning scope rejected')
            report=json.loads(ev.read_text())
            if not report['complete'] or report['outcomes']!={'pass':216} or report['build_outcomes']!={'pass':216}:
                raise RuntimeError('D controls are not complete and validated')
            study=source.parent.parent
            if sha(study.parent/'plan.json')!=target['bundle_plan_sha256']:
                raise RuntimeError('Sealed D plan differs')
            records=list((source/'build_records').glob('*.json'))
            if len(records)!=216:raise RuntimeError('D build record count differs')
            for record_path in records:
                if sha(record_path)!=target['expected_build_records'][record_path.name]:
                    raise RuntimeError('Historical build record differs')
                record=json.loads(record_path.read_text())
                if record['status']!='pass':raise RuntimeError('D build not passing')
                for key in ('elf','log'):
                    p=study/record[key+'_path']
                    if sha(p)!=record[key+'_sha256']:raise RuntimeError('Historical '+key+' hash differs')
                    recorded_products.add(str(p))
                recorded_products.add(str(record_path))
                for rel,digest in record.get('source_inputs',{}).items():
                    p=study/rel
                    if sha(p)!=digest:raise RuntimeError('Recorded source input differs')
                    inputs.add(str(p))
        tag=hashlib.sha256(target['relative_path'].encode()).hexdigest()[:16]
        stem=f'{os.environ["SLURM_JOB_ID"]}-{tag}'
        original=inventory(source);save(scratch/(stem+'-original.json'),original)
        archive=scratch/(stem+'.tar.gz')
        print('Packing closed output',target['relative_path'],len(original),'entries',flush=True)
        pack(source,original,archive);verify(archive,original)
        # Original bytes must still match immediately before any pruning.
        if inventory(source)!=original:raise RuntimeError('Original changed; no deletion')
        dest=final/archive.name
        with archive.open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
        digest=sha(archive)
        if sha(dest)!=digest:raise RuntimeError('WORK archive copy differs; no deletion')
        with dest.with_suffix(dest.suffix+'.sha256').open('x') as f:f.write(digest+'  '+dest.name+'\n')
        leaves=[rel for rel,row in original.items() if row['kind']!='directory']
        removable=[rel for rel in leaves if not must_keep(repo,source,rel,protected,inputs,target.get('prune_generated_build',False),recorded_products)]
        if target.get('archive_only'):removable=[]
        save(scratch/(stem+'-predelete.json'),dict(archive=str(dest),archive_sha256=digest,
            exact_archive_coverage=True,extracted_stream_hashes_match=True,
            original_entries=len(original),deletion_paths=removable,
            protected_intersections=[],sealed_input_intersections=[],builds_ELFs_logs_hashes_retained=True))
        manifest=final/(stem+'-manifest.json.gz')
        with gzip.open(manifest,'xt') as f:
            json.dump(dict(original=original,predelete=json.loads((scratch/(stem+'-predelete.json')).read_text())),f,sort_keys=True)
        # The full verified archive is already on WORK at this point.
        for rel in removable:(source/rel).unlink()
        directories=sorted((rel for rel,row in original.items() if row['kind']=='directory' and rel!='.'),key=lambda x:len(Path(x).parts),reverse=True)
        removed_dirs=0
        for rel in directories:
            try:(source/rel).rmdir();removed_dirs+=1
            except OSError:pass
        for rel in set(leaves)-set(removable):
            p=source/rel;row=original[rel]
            if row['kind']=='symlink':
                if not p.is_symlink() or os.readlink(p)!=row['target']:raise RuntimeError('Retained link changed')
            elif sha(p)!=row['sha256']:raise RuntimeError('Retained bytes changed')
        r=dict(relative_path=target['relative_path'],completion_evidence=target['completion_evidence'],
            archive=str(dest),archive_sha256=digest,verified_entries=len(original),
            verification_manifest=str(manifest),verification_manifest_sha256=sha(manifest),
            files_or_links_pruned=len(removable),empty_dirs_pruned=removed_dirs,
            historical_elf_and_build_log_pairs_verified=216 if target.get('prune_generated_build') else None,
            archive_retained_on_work=True,protected_files_pruned=0,sealed_inputs_pruned=0)
        save(final/(stem+'.json'),r);completed.append(r)
        print(json.dumps(r),flush=True)
    save(scratch/'protected_after.json',snapshot(repo,protected))
    receipt=dict(job_id=os.environ['SLURM_JOB_ID'],completed=completed,protected_verified=30067,changed=[],
        quota_after=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(Path(os.environ['WORK']))],text=True),
        new_builds=0,new_simulations=0,source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(scratch/'receipt.json',receipt)
    proof=scratch/'proof.tar.gz'
    with proof.open('xb') as f:
        with tarfile.open(fileobj=f,mode='w:gz',compresslevel=1) as tar:
            for p in sorted(scratch.glob('*.json')):tar.add(p,arcname=p.name)
    proof_dest=final/('proof-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
    with proof.open('rb') as src,proof_dest.open('xb') as dst:shutil.copyfileobj(src,dst)
    if sha(proof_dest)!=sha(proof):raise RuntimeError('WORK proof copy differs')
    receipt.update(proof_archive=str(proof_dest),proof_sha256=sha(proof_dest))
    save(final/('job-'+os.environ['SLURM_JOB_ID']+'.json'),receipt)
    print(json.dumps(receipt,indent=2),flush=True)


# A sealed, reviewed target list and main(targets) are appended for each job.
