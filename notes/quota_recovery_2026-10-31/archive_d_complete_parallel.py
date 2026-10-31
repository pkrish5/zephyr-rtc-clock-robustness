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
    # Same manifest/selection as the serial implementation; eight bounded
    # directory readers avoid serial Lustre small-file latency.
    from collections import deque
    from concurrent.futures import wait, FIRST_COMPLETED
    result={'.':dict(kind='directory')};pending=deque([root]);active=set()
    def scan(directory):
        rows={};children=[]
        with os.scandir(directory) as entries:
            for entry in entries:
                p=Path(entry.path);rel=str(p.relative_to(root))
                if entry.is_symlink():rows[rel]=dict(kind='symlink',target=os.readlink(p))
                elif entry.is_dir(follow_symlinks=False):
                    rows[rel]=dict(kind='directory');children.append(p)
                elif entry.is_file(follow_symlinks=False):
                    s=entry.stat(follow_symlinks=False)
                    rows[rel]=dict(kind='file',sha256=sha(p),size=s.st_size)
                else:raise RuntimeError('Special entry; preserve original: '+str(p))
        return rows,children
    milestone=10000
    with ThreadPoolExecutor(max_workers=8) as pool:
        while pending or active:
            while pending and len(active)<8:active.add(pool.submit(scan,pending.popleft()))
            done,active=wait(active,return_when=FIRST_COMPLETED)
            for f in done:
                rows,children=f.result()
                if any(rel in result for rel in rows):raise RuntimeError('Duplicate original path')
                result.update(rows);pending.extend(children)
            if len(result)>=milestone:
                print('Read-only inventory',len(result),'entries',flush=True)
                milestone=((len(result)//10000)+1)*10000
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
    # Archive names/order/metadata/content and link handling are unchanged.
    # Prefetch at most eight members, never following a symlink. Large files
    # retain the original streaming path; smaller buffers total <=128 MiB.
    from collections import deque
    import io
    def read_member(item):
        rel,row=item;path=source if rel=='.' else source/rel
        name='output' if rel=='.' else 'output/'+rel
        s=path.lstat();info=tarfile.TarInfo(name);info.mode=stat.S_IMODE(s.st_mode)
        info.mtime=s.st_mtime;info.uid=s.st_uid;info.gid=s.st_gid
        data=None
        if row['kind']=='directory':
            if not stat.S_ISDIR(s.st_mode):raise RuntimeError('Directory type changed during packing')
            info.type=tarfile.DIRTYPE
        elif row['kind']=='symlink':
            if not stat.S_ISLNK(s.st_mode):raise RuntimeError('Link type changed during packing')
            info.type=tarfile.SYMTYPE;info.linkname=row['target']
        else:
            if not stat.S_ISREG(s.st_mode):raise RuntimeError('File type changed during packing')
            info.size=row['size'];info.type=tarfile.REGTYPE
            if info.size<=16*1024*1024:
                with path.open('rb') as f:data=f.read()
                if len(data)!=info.size:raise RuntimeError('File size changed during packing')
        return info,path,data
    items=iter(sorted(original.items()));queue=deque()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for _ in range(8):
            try:queue.append(pool.submit(read_member,next(items)))
            except StopIteration:break
        with archive.open('xb') as stream:
            with tarfile.open(fileobj=stream,mode='w:gz',compresslevel=1) as tar:
                count=0
                while queue:
                    info,path,data=queue.popleft().result()
                    if info.isfile():
                        if data is None:
                            with path.open('rb') as f:tar.addfile(info,f)
                        else:tar.addfile(info,io.BytesIO(data))
                    else:tar.addfile(info)
                    data=None
                    count+=1
                    if count%10000==0:print('Packed',count,'/',len(original),'entries',flush=True)
                    try:queue.append(pool.submit(read_member,next(items)))
                    except StopIteration:pass


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


TARGETS = [{'bundle_plan_sha256': '61b8715bce7400dc5a380599731f970d8657defb946584875973cdfde81e6518', 'completion_evidence': 'tacc_work/20261024-d-cache-v2/d-cache-v2-bundle/study/results/tacc_phase2_d_20261024_v2/report.json', 'completion_evidence_sha256': 'f675618f261449bf3fba801806f08217bb39134e8f9ef4c734670b83a97a70f9', 'expected_build_records': {'0000.json': '73c6eb500e2468c5fba64e6c46e04c2639273055c0110ff08a0067e9e7a8c0b8', '0001.json': '979d1d1e3d520ab532ed18b5545fd2e5c0b1e90b568154b26c27abc7bc69f737', '0002.json': '31946407a08bdb4739f2027ff6f1c4ce395cd8b71e3f030c947c34802cea0068', '0003.json': '695135ad001ea035ffa5517ed7c99bb9430eaec39cfec51f754979ec3ebb466f', '0004.json': 'ce62227c7d1042a5dec4aa0ae43cf5cbf17a270b739bc11d966d82b29c2ba3a7', '0005.json': 'af9af32e1a0051cab34b7ac4a53fcc005af4083f938c9196e28efa2ccb6abef2', '0006.json': 'e211231167dd770da078d951e4b807347bb5b42f750788e9f4a14bff95e7c3a4', '0007.json': 'a00e9597e2af719aea648bba8e5d05651f870b9d68985b96d983a39297b47053', '0008.json': 'd769267aedc51d12b36e60687121c253bd81af298b23d2432acd5ee283c80314', '0009.json': '10bd5ca04f7654cb8847df0afbcadedc401f68ff16e74978619984d0f91084a0', '0010.json': '8cd2c75746db0ec4e2c242148a893169ba1fdd6e50ffc335b678a417341765ac', '0011.json': '4405e77bb79db50db05d6ccc3f0f50d3083e2a6896923d186edff8e8edf2f1f7', '0012.json': 'bdbb089281a613b1574727f1567811f4e27281b122a69b6af2e271271eee769b', '0013.json': '8ca8fe081cb174c015c66eca8c74c520145bb7d4cddcd46d9e48ca259c86efd3', '0014.json': '7204a90f570a8809c537f915b5246220aead3e19892e23623e2986e06720c617', '0015.json': '11456b784a579ef67a1d5ab8ca9584373478a979eaf50b423e7d579a355640f2', '0016.json': '7404590a5bb54bb27c61b84604b6fcc99bef751a244dbb3830cc48c05a219982', '0017.json': '38b471925c071c30012e8228225a2d445fcb56ca7ed1d08b1f6413d9aa97b273', '0018.json': '61ed3c0e6767819fdd96b5507ad46741f449c88b04fb1e6296369fab6d8ad160', '0019.json': '51ab75b43ae66829d46fc9966c197101e021ff9d84e2eb45f1db2321b7312f45', '0020.json': '62232ea1a32320f3cf0a54b86793d3eb3b0146065dccd0383eec1ebccc0de901', '0021.json': '22fb78f39c9f8b758c7e39f5f6209808ab25f148414cc6e1de50cbee14d4f39b', '0022.json': '7bdb9b77680870e543df42d60c7cbd51c399ce26ea37aa47cce79c91819335fc', '0023.json': '5d430b2cde2e32fec5054b4d17bdf542a182ae6527257268d9af7ae009bf8b92', '0024.json': '396f64e87e5a1075998ef07483fb99d13794858abba07c32f2f3b06f3886f6da', '0025.json': '8ed27c222c3db6343fdac57336395947e35301c3cdd0b78115afa79a0e2a9734', '0026.json': 'fe953a82657058963495ecd3351a211523500858809da9beb1480fc407c30110', '0027.json': '7fab1b1a3d687c5b85bb0d649821d24fd3ff1780029e8c050a989045dfac3273', '0028.json': '4be53b4e4246e94698c5ae067fb6830042d9b8c16703b20cf149d179a65eeada', '0029.json': '89e0361e65f1416b0c8de9558e748a92a8501323dae62f9c3e1231db349ccc2d', '0030.json': '53f39635696662cfe0d42f91c8df5145ed236d254e336ece225c3befa34d008a', '0031.json': 'c053ac3d73509857ad3d3d4820f1a8189465eaa80edbe023d8d3006dcbdfcba6', '0032.json': 'e6a81577bf5019b1550561cdaa3ce55ce8c8aa3f2aaaeebe0760192380eb6bf8', '0033.json': '408bb94b3418335cc159135263b708d61b2385ec221e3141f6b92d16d771f506', '0034.json': 'cedf1aec05c5f15b5438756d40afb86fcf11cf653fbdabdd5667a1aa9d37eb81', '0035.json': '30c776e9722e32134f4a7b753fbf2299818fa5e1ae38d2dea4e8f0da2d508299', '0036.json': 'ae18a87e36448947435cb2445bcc45f158c8234943906f8af24d75322df644b1', '0037.json': '458059e8c3968d5cb267c0b9160f24d4a98e21b3b64c5d6b63de68f9f6f291ea', '0038.json': '7a707e38e1b3eb9440289242832443c2f79983c1b7a685e210890acc2452d729', '0039.json': '71410bdf690131f1a2a571231fa15777afa2e67ec4a9a01f9c0fd1f30b6feabd', '0040.json': 'ac7c1457e0fdc9e8fe5690b27e41f78b7aeb0324920f6eb963437ed6c5041a19', '0041.json': 'a5bf1ede7ade3b426ede9b960adafe4dd56608dff62be95ea2ba962ee067c3e0', '0042.json': '5e3b9d17c95a94bb459afccc162a977296e4072f113539c36ff07867bb82b732', '0043.json': '736da2cc7e7abc4f67bf0e4bfb2268f1710509b412cb918ff8655d18d5b710a5', '0044.json': '6a5cb080819b7625eca0bbc61cea5eae32082489c3092dc8fd1d6ddd7287a5cc', '0045.json': '61d39c6fac271d530a37cc149d5306b2bf41b438772eb448bdf070c3c46bf7b9', '0046.json': 'cb8d61f4df11a0a9d76606150b062123796685f0a5398a060cda00ce486cb953', '0047.json': 'd9514f0d6c0be9890c18f7cd57760da53a69c5100ebcdabc47ae10e7d99a0e83', '0048.json': '372d217daca7b5e1309e4bf96a5e33c8f1a2d828433fc2e7961c9bac9106984a', '0049.json': '94372f490a09ff527824a6e7d0261bc82462c8ce47a70b878e86ced49a3bdf60', '0050.json': 'f87531b3841d6f49cf606790a4067c147b33bb8d674f7779e0edc0e793355903', '0051.json': '594abe5d89c89eae249e232cdb7666ae05f14ace460382456cfbc5821265702d', '0052.json': '95632f690c295728fa1c120f515bca8c30d3f618c7a238b78fb52fa721d5c6dc', '0053.json': '54236eac6c1e5248ed3e0ded9e42bd8daa3b314754179e0a64b783c5faf50dbf', '0054.json': 'ff10bc2aba36a8971ba41dc4305da443fc132fb0d8a5993d91fd45e93b8b790b', '0055.json': 'eaf09701be4f686d4f0621d678f2aa15ea1407b11ea8fe7397f8478dc1b26c77', '0056.json': '689f9e7f174a856530438c6116f4a2cf1ba0513a713df7b96553cc45528c78db', '0057.json': '30097af81b24e9586d339024abd69bc735da6273bd3f05c0da13af995c2a4938', '0058.json': '2894a65247101432ff394b1b2ee0520211fe75db27e296c6ea09a86c7060e901', '0059.json': '409a72ca22c1fe792175aa834ac439022a49b1b2e17ebc2010b165aff57ddb92', '0060.json': 'bb04e4bdadebb7a1614be6fb78ce028985caf93230edb061bb5fb5fc34633e78', '0061.json': '971502bd830709961acfe40b5669698efeab20cfe6068c149c9c134e7bf9b016', '0062.json': 'ea2d70a7d281ed8f04cd72384d51b0ed2def7ac54d05cacf46f5de860f19d653', '0063.json': '23c5dc9f4c76f7eb29cf4bd581ae008efef16e0aec7653eb7ba9a441b73b8daa', '0064.json': '835d57f192d5f801a2007cefb86d0ece564b7fdea1d981b065bea7609eed2724', '0065.json': '9e743c15d66b0dc85cda3f3e62650a6b0261d19807180f31a980350941676c73', '0066.json': '56c0ea41c057872cf1cf6406721dc45da53d8cd228930a56f2f5c75260c305f1', '0067.json': '3bb0ab8130cd64660d82723e9db8a725054d720dbdb6046a3e80793aa1c549ef', '0068.json': 'cfbe0cbaaa7e1744c296cba966ec7026e1cb9de51b598c88c72bdba9a3b61e28', '0069.json': '08a750bb63a984995f6cbca06e93f2c725f8bc2d203c3b43a9fbf283e2b08e97', '0070.json': '7342d9959a98fec69e070c1bcac7585a7c2adb862e055cb9b958b2a410d14ce5', '0071.json': '6abe44da60e280b0321ced87b4c13d7170626ffb776569941974ca67b25c1a87', '0072.json': 'f112d86ead40ef5caa97f56f9fe73bc4e2df82908730992f2bc98c55d9861210', '0073.json': '68325247c16d2374145872b70cbfe94d5042c929b1f725166c1aaf4a95e4224a', '0074.json': '6d8ff13239e393957832907e86507409f77b3ad024e7d070686696ce51ad251b', '0075.json': 'f33c6c29193299a076519ee5e544a994a34fb30bd1786f47c9dec122cd5ec0fb', '0076.json': '09bad44e8b616ba8183a3f6dff65f94496247816b987820929eb3c125080b0b5', '0077.json': 'b8808bc99f3b185a3c8d48f39958ecc472c7d708af1f5cea9d1bdbb314f7ce95', '0078.json': 'd7f6ae0f6a75763c78b2afc48b00c9fa574696acd6aea50b9eddd1923e7c8e9c', '0079.json': 'd00e1e605a43b23573af00d296613ee71cda9710d97e58c548d86da916831f63', '0080.json': 'd753bea03234e1b24c1be9825ca058d93e79a3185a74d3abeddb318f5c2f3f03', '0081.json': 'e147c1778b717929803a55847c7553b1cd49ac48e4844475852a2fa6c66ae1c4', '0082.json': '20ed7eba6fb44659ba291cc791f27d78c07c121d0e9bebdecdf7ef92c0361d2e', '0083.json': '466c5a5406e139630b2d3c173d6cd63429a3a21773726797e2b0c3c5534629ab', '0084.json': '716caad64e87bfbe83ab594768defce86f695df568490fbf11a9762f2060a5ad', '0085.json': '6db7613c5d1e7002dfe2b30236e0088a92812ab1982fb55a186304a9b1b9ea3f', '0086.json': 'c2da41498a3b7bcbd004d2cd22cc978c90a6922b2c8bfc52971a1c1e267a8411', '0087.json': 'e18d1f1042232575c1882bb395590d5113bb9e6f095f7c0d53279dbc75e47c67', '0088.json': '4e5f438ee0e850b03a088f6c72ca56eda8e099685b7dee48df1c5bec5fe5c99e', '0089.json': '8cfb092c09188ffac185aa12f4955a327ce490f425f0f6f73d888a04ec51c0ac', '0090.json': 'bc823dc95686b6eccb8e6aa23bf48b1e19d68e91263a9c2e9cca2d4456beafb5', '0091.json': '1f723043071c902f8bae1f6f5d81fad00f4b2aee8165fe4a12dec651e489c717', '0092.json': '86fbd5631a99b48ac0c78fdfbaba3c7bcc552df81afb450f6a794cc00373b2dc', '0093.json': 'b25da1ea69d5d574ea10be697d2524eae1741a9d986ed4b5bf9e4ee2e74ee49e', '0094.json': 'cd432b639ec527353cddf59f02e50d86f1576d702918549ee14eaa58a130a407', '0095.json': 'b1540cbe79af4722e648419d0605f25a6fe2abae2cfe03a0f44c73be965caef4', '0096.json': '908ea7adb88f5a45a0040a721e5edf90d4a72082a4d3400fd84a0b3c981d9cf7', '0097.json': 'af88c703104b2dbe24d86dc92f9afe7dc2be085ffe61ceda7392d06292b0b498', '0098.json': 'e78f348b6e2079aae5c5a6e49647b8bf22617cdd1f082dc754794cc1db071ee7', '0099.json': '18f12b338e30dbd8690bab200d047f363861d8a96cfd5bee91db5a2b7dcf9978', '0100.json': '1b873302a6fe2a3ed0a2e06ebd6afcf81a8547c796b8af54d8920062588f3d97', '0101.json': 'aa87a9276a3dc94ca2da045ba9b5b48f87203f5c4418b256ebb2e715d50d2d18', '0102.json': '14091bf2b78dc1bded42ef4ea95bffc24fc0d891d09f025f346a5d31e163a87d', '0103.json': '74cb98e4d2cff4746cb7fb83677a95dd3a76d59bc02d35cce402478f02afc97c', '0104.json': '6e00f67da3ee21f7c4fcceaef15792be97f2939687507392a3bc48c33d0ba2a3', '0105.json': 'add631f71c1a8093bb2e2ee8ae5cedfddc1d845eea7d518be738eb8180eb8b20', '0106.json': '57f702eba1f4e6baad026daf29c78a308d4b7af3e874e13fcbd8c6a0fc319843', '0107.json': 'e7b29254f4eef9d7b85019ee01b6d6f3797825768b8e07e1eeda6fa6157c4a9c', '0108.json': '673b4a8dfb76dae82a56073ca7267160554cf6ef865ef7bf599483bf0e1e9018', '0109.json': '1e04e25ae2cf8a8b12407785942b6071ea600792392b0019cc0d198ea227e454', '0110.json': '10ffbc4bd5861c3973e0be5cd84e45b73bd83cc2c8ad184d387a5c5ee22f651f', '0111.json': '6141ef5950c7943960758bdc8def4b8c7d482f00af6c10593f219f7c68848e73', '0112.json': '7fbf75507b0c1fbc191100e2ac4930ed6ebc0d8fc3972e5596b1d99e63e8de7d', '0113.json': '3d1fbb92b5813187d4840aa1618d5aedf5b3ca98124446c3e60370e4a6487bd2', '0114.json': '7a2e85c4aca61d7c5332e61f3dac43f9893fe031453ffc1ce0ef12235ca3dd6c', '0115.json': 'a34780701b4e87a0bf4cef0a749d0f68c0db2c6f09fdf822f7b8741d4dafa113', '0116.json': '235a2536cbb1827b3789ee271ca2c09b0f4adef9b89c9b19951d61b7740b9020', '0117.json': '20a0aa1bf871424df4b3e783bc380ce4018236e1b7455c0df261977f57b24e5e', '0118.json': '904d15780da47c75d83d78344fa41eb855b47f890284d799e7dfaec1976c8844', '0119.json': 'a6eab452633c50299c81733abc514bfec822d247f6e851436e5ec1e725ad17b3', '0120.json': '52ee0a4e8f600471f7cfc74237e8fcdccdb2483ab159a605c100b5d53800270f', '0121.json': 'de7cae7328549655b3474d03ba15fcf2869c9aa6229722944dad74f64553c628', '0122.json': '889e3c7b72b7ea81cacaf14417f18e511c59603e26c0ed44fafe3a8175e1ced8', '0123.json': 'f459d8ba18aefeec09101d3d3d69cd0e070481e5f989593a589abb0c8470f0de', '0124.json': 'e35eac0e80d5b04391c9ee71666a0c112133d9e668f92adb51b1d09bef712fd7', '0125.json': 'ba7112b32fd9108cbe40aee5c89310e9261f6ecf39b6efcb0cba3c20146d51d2', '0126.json': '62a9444e7af8acbe89cf82fc5313351fe771d7d0ba599f59d91ec03f23803354', '0127.json': '848d16969c38ca407f38348e9ac16becb3a6e5b47baff05e3407439c889b105b', '0128.json': '58cbf399da4a4d4be009ed5efc2dbc6a3539f42603d4b932a7b45207d1e13799', '0129.json': '7b567d0f0d097416b58b6aa7f75a1ed2dc6d4ecd3f968b7ed1f1283f7b0ac4b7', '0130.json': '21a62242482d9380018b3208bbf48b4db1d1b12f2b1f55da8993a4930d4522f9', '0131.json': '0c973d6d98c6d9ffc24e40c9aa44ac46cb13d16906daf6aaa7c62142be4e5c01', '0132.json': '3c88bf25744116a0e4db146bb66550b9cd0e45bed70bc433a6fc103fd14c18dd', '0133.json': 'b57bb24fae49e774bd347d21d669be05d0afa0674f6c13532ed65b4a91d451c2', '0134.json': 'bb883c9fdb7db95f028a7bce063c6653ee2542aeb5d61885ea9f8e7df86d3ac1', '0135.json': '57f127363ef5bab4963103916e715ae963a1a29c7cd91c3e0dcf5512ea33ee8e', '0136.json': '9b295f1ad6309fee779bbe97d8f787d77949441ba8c6c3399170b87b7dd0c643', '0137.json': '0878db4558b22eceb22b17a75f74f7b8e7928588e42957a8c5713c62fc1b6c2e', '0138.json': 'b016998f453ef4406ed9b2061d51f32577a54858f502239db9e2847866ad1bbf', '0139.json': '48e71f40bf03ba8f08e838c47983ee8feab47ba99ecf0eb66f0ffe59df6c795f', '0140.json': '74cd5858514815e9b03ed0abf9c03dfb767caba3b1beb5d6dbccb59acd295799', '0141.json': 'f991f5805715c78c2416d3926dd4a387b599905c120a63e40ab8d440608e50a0', '0142.json': 'c8ffbeb35b13746ba95c2ab5e627e540c3d82c02a0aec6cd91e87dbaa11ad3a6', '0143.json': '536450e2231d896c4daf9f99e21410ba0c72cf7f6194c1b5ca3ce4ce64ca545a', '0144.json': '56fee99098b88160a8aa5bf58f19204b265a9298bd4321df8ca42953a34bd421', '0145.json': '6cc9f779b5b3153e6fe259f94bd256b7f6fc103806148da3d520d6ccd7f56de6', '0146.json': '969d19ed71598f03e05d16438173a6f33ad5fe2ff5018a5333d16e0f757f1277', '0147.json': 'c50dbf6c75c7578470bbca5d1535f9fefaf672d31b18531843f6a2f62f2c567b', '0148.json': '0e810ac450f9af1c01b891a3bf27b05347a1512406ce65b88ec2ed34494ce45b', '0149.json': '642bdb94a0c80f893229fa327ba6cde11b236b7d5095dc8fdecbbaf98f73c94c', '0150.json': '32d2d173fce51ff57136af99539296b80ad3355d31f38a940f1b4f26965b4e9a', '0151.json': '06919892fc89d2b73a05c4d50ba451d7b40c8281dfea8b3e06a330a1cd6f17c0', '0152.json': 'd6f0fe5c5f8c2f545ff65259277ecb45555fbdf4a1ca674b275a2019a0621b58', '0153.json': '0a16bf8d00f6dd4ddb82d5add7828e7a65a6eb800829faf35b9ceed21e716498', '0154.json': '6ae53645de14f6b593783c6ff0cfdc1e43d42851ca1dda48a2b890d07587dcac', '0155.json': 'b81e04a21deb74417d8edb3e68d2b28b96059381993ea4fa70544bfbfbc6aee9', '0156.json': '91ad9523aeb6e7cafc92fe5aa95ed7679d8d4331351b9043dc5892e34171d50d', '0157.json': '9a3ec10b9bd9c1ab0b794fb2d3db9cb00a19669ba73966f17a5cba93a27d83a3', '0158.json': '1d028c3f270936783c770afad4fa966dd01afd0bff5cfe4e7eac6c64e977f464', '0159.json': '7debd9bd8c0d4f3d426d1883137090dec8335debf098817196ed2a8b1659e54c', '0160.json': '798470ac17ab011acab95236f6ba9f568465d0a62be856a96503fd76300f5cb2', '0161.json': 'ed2a6fda1e8c81ce8a582a0ecf6ac2a4e886c30d99e139993b79dc91c395d01f', '0162.json': '1e0a09d458e745ab0e376d7f7a3337f32bb328ca43416ea36beb9e36f35595f9', '0163.json': '496873edfa263be53df7018301e8dc7c53e0bd1b26ca290cb020f2eae61dc16d', '0164.json': '680428d6805c6569602a148638cba8de0fd8803c213f127b256eb4b47623e5d9', '0165.json': '32d54656b697bb6676dc21fe95983ec2808f77197d5d689dae5ef0d7388f7893', '0166.json': '3dffd181a1a237e4c6e23f61999b6b1582d5d49004130577276262e5996ca425', '0167.json': '73e9c3c7bc6cd0b426c2f5e99e15b1da2e7e9907179a00515752e92bc0d36232', '0168.json': '365b3feb0f02b91bdf40420fa32f0cd987323c6e41bb2cd018efc6963a66964f', '0169.json': '10f30c8996c96e48afc4fbb10689b8e085925acb3159834f9d73e58482a82b9d', '0170.json': '986fb37b0fa87739750ce59f97784b8e1befb8a04aa775c17ee494722b98b401', '0171.json': '0beb27f8870d467eb04bf6b832cdfc49ad1d76da6227e6e16f5eb2b40f23a524', '0172.json': 'f9f7182c508194b866aca068224b4d1df095a85b00b0ecb8b2cabbf045db71fa', '0173.json': '1e3f698535e8ea53754989fb4a5b67190137c9232bfdab04db2d7a4c507e95e0', '0174.json': 'd7afbded6886ab9537fe669df74c76072e2a62f1a5e03d741fd7e8da9dbf8877', '0175.json': '6e84843831c61b46542ddeda6be689bd951c4d2443bf8b81b619069e321ebb39', '0176.json': '2a83065cfa14316aa16716a29bf67260655c26967b19211e673dec53fe737a9b', '0177.json': '6a1f65c70266a6db7d6474cdd9a2ffca4a190c33202535ea5938908bfdcec164', '0178.json': '511ac98ff9122a1070445ec56a432cb8a18b1e98ecbee287173ada775e6aa423', '0179.json': 'e2f911feb900535a665433226aae847e5464c863d92d0574cd6d2372e1b6c90f', '0180.json': '490f725a889fda11f99c7edfafcd480f5ee250ab239ecbda66cf3c6e05c5379c', '0181.json': 'def1a03453f99b1584f13ed83ccb2088941dce9ea1603e7206722988e3c40d40', '0182.json': '55322d76d1e9fbf1ccea576888976df9664141a28299407219a63250d136f241', '0183.json': '90c51be8efea3318ade8b4cd95189448f5ced17794bba5bbf90ba768111e572a', '0184.json': 'd7d36d88344dfba246605a4f00d879a0a4c879a5c1236d44db8f97865c7e4393', '0185.json': 'b67459064f5a3878f009008db347e01442785d16534567078872c999a3dce715', '0186.json': 'f61e4662b0e36de665e0ec1f3f8ec9ebb0acdea10d09331f601a3d51d0c075fa', '0187.json': '012ae6db070598ec554eee8b9db57c65d5c64160c98859b9ea38ae5ab663d2d9', '0188.json': 'b1771becde7a2521143960b6aa4c27cb80f503bf872352c8ea9670a871c0ca4a', '0189.json': '8a11a77e5859d157b0112459e3393d75d6b3eb8f05f76e5fc5e9354e301b42f8', '0190.json': '66a191091f52eaad66ce618e78a1c3e1c2c973757e92c699564f7d3e157a0661', '0191.json': 'f56cdfd4abe7e5792627ee838bf8368af954cb43cce27e2fa7e33e59ac260ad6', '0192.json': '534218b6204bdbc5554c932325c84a711c9eab4f2a6c52486c4b9a0aabf81e20', '0193.json': 'c74ef545f6d6389ad991acb75d62e5d3d8ac9e022984663acfb6aa6fdbf17024', '0194.json': 'e0717d07fbd6afb6f138cdd526a26bfa8292ac30bce29ffe65cf238e1678caa2', '0195.json': '8781f95689b58d9abc1ab2bd84d20230c19f4ff27f19ea70647ed0b2869a6dec', '0196.json': '5b4887a3e46141fd68e3d747fb2eb8af94d01355e9b523be6884b95c9179dfab', '0197.json': '5e8e42fc904d0dfabb69f826a97ce47e510a504f1a7797e7d60bc4087bd46526', '0198.json': '47071eeab3b1ad8e3c29bded0de190eb40bb21e81c1f2c7ea947fdd68408e2d4', '0199.json': '2cc9ce6088b0a9eb957b8e46110137cdf307af0eb5f1ca5e2b8a986316bc5baf', '0200.json': 'a45d5bd8ad928acd08bbe63a36bb4878cb4733cbffda440fba17d15e929fd016', '0201.json': '9d7549576484da081c40458a2c7b200db882f259b010af46574f1c44308a7f6f', '0202.json': '4f18a71aee3ae1f23ed2e66452e4c4c69cc7675379b1c0a3d5d16f25355b2d4a', '0203.json': 'd17975a70a828d16895ef66a98f3cc2a914ef71aa43dee91417314fd037a3496', '0204.json': '40679e16a6bb71a52f39b1bdce436ea73aa76f03bb693df7495cc31c44a679a8', '0205.json': 'dddc1c8e13fbca4940388c49ba9d5fff83f0550bcb1e1d7b4bbc2fb401d62057', '0206.json': '0613b81448e72e8669baaced5dad4698bfe22edf1abda7287d078fe941f43cb9', '0207.json': '662e060b520c0ef472555d04906d9dc3d8ce1fea871e779884b9e8b5b8b33cce', '0208.json': 'a487d56679af2227f2997cff330dc3c0cf2c0388af022b803a6dd4c764ac1e2f', '0209.json': '76677d7aa84794671ddd4b816676e32687f11de1bdc9cfaf5551f13280728388', '0210.json': 'e69dc94fec48d40c8cb1f421022c2e8f53fdb1250ba01fe21e3db55169402067', '0211.json': '8ef8e66a78f4f07cac2338b9be6bdd175898c40079e56764a06681070e8b32ac', '0212.json': '752d5cc6e6fd00d64d9c97394f8114f32d2c9f87374abe6e62b8a55a67f86734', '0213.json': '40c4d1a4258237370f1efffc4f3139415b51e4d12b8414545d1863c1d028fcbf', '0214.json': 'cc0a6bbd5520531c0f9e871cfc6e0f517e585fea1fa76869a851520d4afbef9e', '0215.json': 'bbf0f898a0fe73b7982674878c2fb1a542a411553a3199be17ba8c70269ba2e3'}, 'prune_generated_build': True, 'relative_path': 'tacc_work/20261024-d-cache-v2/d-cache-v2-bundle/study/results/tacc_phase2_d_20261024_v2'}, {'completion_evidence': 'tacc_work/20261024-d-cache-v2/d-cache-v2-bundle/study/results/tacc_phase2_d_20261024_v2/report.json', 'completion_evidence_sha256': 'f675618f261449bf3fba801806f08217bb39134e8f9ef4c734670b83a97a70f9', 'relative_path': 'tacc_work/20261024-d-cache-v2/runtime', 'scope': 'closed D control per-run homes/cache/temp; no E runtime or frozen bundle cache'}]

if __name__ == "__main__":
    main(TARGETS)
