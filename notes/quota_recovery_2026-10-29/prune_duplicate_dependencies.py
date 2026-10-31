#!/usr/bin/env python3
"""Remove only verified duplicate packages in the abandoned v5 build temp.

Never removes Zephyr sources, rtc-code, SDK trees, result directories or the
recovery backup. A package mismatch preserves that package tree.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')


def inventory(root):
    rows={'.':dict(kind='directory')}
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(current)/name;rel=str(p.relative_to(root))
            if p.is_symlink():rows[rel]=dict(kind='symlink',target=os.readlink(p))
            elif p.is_dir():rows[rel]=dict(kind='directory')
            elif p.is_file():rows[rel]=dict(kind='file',sha256=sha(p))
            else:raise RuntimeError('Unexpected package entry type: '+str(p))
    return rows


def main():
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development required')
    work=Path(os.environ['WORK']).resolve();repo=work/'zephyr-rtc-clock-robustness'
    out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();out.relative_to(Path(os.environ['SCRATCH']).resolve())
    out.mkdir(parents=True,exist_ok=False)
    recovery=repo/'tacc_work/20261029-quota-recovery-v1'
    cleanup=json.loads((recovery/'build-batch-3541116.json').read_text())
    if not cleanup['protected_after_verified'] or cleanup['protected_files_deleted'] or cleanup['raw_verdict_records_deleted']:
        raise RuntimeError('Cleanup not validated')
    baseline=repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline)!='b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef':raise RuntimeError('Baseline differs')
    expected=json.loads(baseline.read_text())['hashes']
    def protected():
        rows={}
        for rel,digest in expected.items():
            p=repo/rel
            if p.exists():
                if sha(p)!=digest:raise RuntimeError('Protected bytes differ: '+rel)
                rows[rel]=digest
            else:rows[rel]=None
        return rows
    before=protected();save(out/'protected_before.json',before)
    if any(value is None for value in before.values()):raise RuntimeError('A protected input is missing')
    quota_before=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(work)],text=True)
    image=repo/'tacc_work/20261023-v10/images/rtc-ls6-v1.sif'
    image_sha=sha(image)
    if image_sha!='94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1':raise RuntimeError('Container differs')
    runtime=Path(tempfile.mkdtemp(prefix='rtc-dep-check-',dir='/tmp'))
    for name in ('home','tmp','cache','config'):(runtime/name).mkdir()
    probe=("import hashlib,importlib.metadata,json,subprocess;from pathlib import Path;"
        "print(json.dumps(dict(renode_dll_sha256=hashlib.sha256(Path('/opt/renode/Renode.dll').read_bytes()).hexdigest(),"
        "renode_version=subprocess.check_output(['/opt/renode/renode-pinned','--version'],text=True).strip(),"
        "packages={d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions()})))")
    command=['apptainer','exec','--cleanenv','--containall','--home',str(runtime/'home')+':/home/rtc',
        '--bind',str(runtime/'tmp')+':/tmp:rw',str(image),'/opt/rtc-python/bin/python','-c',probe]
    shell=('set -euo pipefail\nmodule load tacc-apptainer/1.4.1\n'
        'version=$(apptainer --version)\ncase "$version" in "apptainer version 1.4.1"|"apptainer version 1.4.1-1.el8") ;; *) exit 2;; esac\n'+shlex.join(command))
    env=dict(os.environ,TMPDIR=str(runtime/'tmp'),APPTAINER_CACHEDIR=str(runtime/'cache'),
        APPTAINER_TMPDIR=str(runtime/'tmp'),APPTAINER_CONFIGDIR=str(runtime/'config'))
    response=subprocess.run(['bash','-l','-c',shell],env=env,capture_output=True,text=True,check=True)
    probe_result=json.loads(response.stdout);save(out/'container_packages.json',probe_result)
    root=repo/'tacc_work/20261022-v5/apptainer-tmp/build-temp-2644144001/rootfs/opt'
    candidates={};decisions=[]
    python=root/'rtc-python'
    sites=list(python.glob('lib/python*/site-packages'))
    packages={d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions(path=[str(p) for p in sites])}
    mismatch={k:v for k,v in packages.items() if probe_result['packages'].get(k)!=v}
    if packages and not mismatch:candidates[python]=inventory(python)
    decisions.append(dict(path=str(python),container_provides_all_same_package_versions=bool(packages) and not mismatch,
        installed_packages=packages,mismatches=mismatch,delete=str(python) in map(str,candidates)))
    renode=root/'renode'
    duplicate=(renode/'Renode.dll').is_file() and sha(renode/'Renode.dll')==probe_result['renode_dll_sha256']
    if duplicate:candidates[renode]=inventory(renode)
    decisions.append(dict(path=str(renode),container_has_identical_Renode_dll=duplicate,delete=duplicate))
    for target in candidates:
        target.resolve().relative_to(root.resolve())
        if target.is_symlink():raise RuntimeError('Package root is linked')
        rel=str(target.relative_to(repo))
        if any(p==rel or p.startswith(rel+'/') for p in expected):raise RuntimeError('Protected intersection; STOP')
        if '20261026-git-checkout-recovery-v1' in str(target):raise RuntimeError('Recovery backup excluded')
    save(out/'dependency_decisions.json',decisions)
    save(out/'dependency_deletion_manifest.json',{str(p):rows for p,rows in candidates.items()})
    for target,rows in candidates.items():
        if inventory(target)!=rows:raise RuntimeError('Package changed before deletion')
    for target in candidates:shutil.rmtree(target)
    after=protected()
    if after!=before:raise RuntimeError('Protected files/presence changed')
    save(out/'protected_after.json',after)
    receipt=dict(job_id=os.environ['SLURM_JOB_ID'],container_sha256=image_sha,
        dependency_trees_removed=[str(p) for p in candidates],entries_removed=sum(len(v) for v in candidates.values()),
        preserved_Zephyr_source_tree=True,preserved_frozen_harness=True,preserved_recovery_backup=True,
        protected_files_changed=0,quota_before=quota_before,
        quota_after=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],str(work)],text=True),
        new_simulations=0,new_builds=0,source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(out/'receipt.json',receipt)
    proof=out/'dependency-cleanup-proof.tar.gz'
    with proof.open('xb') as f:
        with tarfile.open(fileobj=f,mode='w:gz') as tar:
            for p in sorted(out.glob('*.json')):tar.add(p,arcname=p.name)
    final=recovery/('dependency-cleanup-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
    with proof.open('rb') as source,final.open('xb') as target:shutil.copyfileobj(source,target)
    if sha(final)!=sha(proof):raise RuntimeError('WORK proof differs')
    with final.with_suffix(final.suffix+'.sha256').open('x') as f:f.write(sha(final)+'  '+final.name+'\n')
    receipt.update(proof_archive=str(final),proof_sha256=sha(final))
    save(out/'final.json',receipt);save(recovery/('dependency-cleanup-'+os.environ['SLURM_JOB_ID']+'.json'),receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
