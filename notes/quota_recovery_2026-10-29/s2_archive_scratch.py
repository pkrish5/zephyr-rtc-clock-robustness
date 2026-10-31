#!/usr/bin/env python3
"""Run the unchanged S2 collector with its working destination on SCRATCH.

Container binds change storage placement only. Selection and collector code
remain unchanged. The final verified archive and receipt are kept on WORK.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import subprocess
import tarfile
import tempfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')


def main():
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development required')
    repo=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
    out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve()
    out.relative_to(Path(os.environ['SCRATCH']).resolve());out.mkdir(parents=True,exist_ok=False)
    quota=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],os.environ['WORK']],text=True)
    rows=[line.split() for line in quota.splitlines() if len(line.split())>=8 and line.split()[0].rstrip('*').isdigit()]
    if len(rows)!=1:raise RuntimeError('Cannot identify current WORK file count')
    count=int(rows[0][-4].rstrip('*'))
    save(out/'headroom.json',dict(work_files=count,threshold=700000,allowed=count<700000,raw_quota=quota))
    if count>=700000:raise RuntimeError('STOP: restore WORK below 700,000 before S2 collection')
    recovery=repo/'tacc_work/20261029-quota-recovery-v1'
    if not json.loads((recovery/'bootstrap-3540791.json').read_text())['source_removed']:
        raise RuntimeError('Quota bootstrap unverified')
    pruned=json.loads((recovery/'build-batch-3541116.json').read_text())
    if not pruned['protected_after_verified'] or pruned['protected_files_deleted'] or pruned['raw_verdict_records_deleted']:
        raise RuntimeError('Cleanup protection failed')
    job=os.environ['SLURM_JOB_ID']
    receipt_dir=repo/'tacc_work'/('20261031-s2-return-'+job)
    receipt_dir.mkdir(exist_ok=False)
    # Provision only original, hash-verified files absent after the earlier
    # quota interruption. This existing helper refuses all overwrites.
    subprocess.run(['python3',str(repo/'harness/tacc_s2_evidence/stage_audit_paths.py'),
        '--repo',str(repo),'--cache',str(repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1'),
        '--out',str(receipt_dir/'audit-dependency-staging.json')],check=True)
    base=repo/'tacc_work/20261026-s2-primary-v1'
    bundle=base/'bundle'
    plan=json.loads((bundle/'plan.json').read_text())
    for name in ('return_primary.py','audit_primary.py','return_primary.sbatch'):
        rel='harness/tacc_s2_evidence/'+name
        original=subprocess.check_output(['git','-C',str(repo),'show','c258b10833db93f0c9a770d3bbd54900290dc466:'+rel])
        if sha(repo/rel)!=hashlib.sha256(original).hexdigest():raise RuntimeError('Original collector/selection code differs: '+rel)
    image=repo/'tacc_work/20261023-v10/images/rtc-ls6-v1.sif'
    if sha(image)!=plan['image_sha256']:raise RuntimeError('Calibrated SIF differs')
    # Preserve the original registration used for S2 even if DESIGN has
    # subsequently gained the separately dated E recovery amendment.
    historical=subprocess.check_output(['git','-C',str(repo),'show','ea7ab441fb43838f4490f9bd9c2849e14d0ea84a:paper/DESIGN.md'])
    design=out/'registered-DESIGN.md'
    with design.open('xb') as f:f.write(historical)
    if sha(design)!=plan['design_sha256']:raise RuntimeError('Historical S2 DESIGN snapshot differs')
    workspace=out/'collector-work';workspace.mkdir()
    logical=receipt_dir/'workspace';logical.mkdir()
    runtime=Path(tempfile.mkdtemp(prefix='rtc-s2-return-'+job+'-',dir='/tmp'))
    for folder in ('home','tmp','var-tmp','apptainer-cache','apptainer-config'):(runtime/folder).mkdir()
    command=['apptainer','exec','--cleanenv','--containall','--home',str(runtime/'home')+':/home/rtc',
        '--pwd',str(repo),'--bind',str(repo)+':'+str(repo)+':ro',
        '--bind',str(workspace)+':'+str(logical)+':rw',
        '--bind',str(design)+':'+str(repo/'paper/DESIGN.md')+':ro',
        '--bind',str(runtime/'tmp')+':/tmp:rw','--bind',str(runtime/'var-tmp')+':/var/tmp:rw',
        '--env','WORK='+str(Path(os.environ['WORK']).resolve()),
        '--env','SLURM_JOB_ID='+job,'--env','SLURM_JOB_PARTITION=development',
        '--env','SLURMD_NODENAME='+os.environ.get('SLURMD_NODENAME','unknown'),
        str(image),
        '/opt/rtc-python/bin/python',str(repo/'harness/tacc_s2_evidence/return_primary.py'),
        '--repo',str(repo),'--bundle',str(bundle),'--image',str(image),
        '--dest',str(logical/'evidence'),'--slurm-logs',str(base/'slurm')]
    env=dict(os.environ,APPTAINER_CACHEDIR=str(runtime/'apptainer-cache'),
             APPTAINER_TMPDIR=str(runtime/'tmp'),APPTAINER_CONFIGDIR=str(runtime/'apptainer-config'),
             TMPDIR=str(runtime/'tmp'),XDG_CACHE_HOME=str(runtime/'var-tmp'))
    shell=('set -euo pipefail\nmodule load tacc-apptainer/1.4.1\nmodule load launcher/3.10\n'
        'version=$(apptainer --version)\n'
        'case "$version" in "apptainer version 1.4.1"|"apptainer version 1.4.1-1.el8") ;; *) exit 2;; esac\n'
        'export APPTAINERENV_RTC_APPTAINER_VERSION="$version"\n'+shlex.join(command))
    save(out/'command.json',dict(command=command,collector_unchanged=True,selection_unchanged=True,
        destination_backing='SCRATCH bind',historical_design_sha256=sha(design)))
    with (out/'collector.out').open('x') as stdout,(out/'collector.err').open('x') as stderr:
        subprocess.run(['bash','-l','-c',shell],env=env,stdout=stdout,stderr=stderr,check=True)
    evidence=workspace/'evidence';archive=workspace/'evidence.tar.gz'
    expected=(workspace/'evidence.tar.gz.sha256').read_text().split()[0]
    if sha(archive)!=expected:raise RuntimeError('Collector archive checksum differs')
    manifest=json.loads((evidence/'files.sha256.json').read_text())
    actual={str(p.relative_to(evidence)) for p in evidence.rglob('*') if p.is_file()}
    if actual!=set(manifest)|{'files.sha256.json'}:raise RuntimeError('Manifest coverage differs')
    # Verify hashes of extracted archive contents, not just the source tree.
    checked=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or path.parts[0]!='evidence':raise RuntimeError('Unsafe archive path')
            if member.isdir():continue
            if not member.isfile() or member.name in checked:raise RuntimeError('Archive link/duplicate')
            checked.add(member.name)
            relative=str(PurePosixPath(*path.parts[1:]))
            if relative=='files.sha256.json':digest=sha(evidence/relative)
            else:digest=manifest[relative]
            h=hashlib.sha256()
            with tar.extractfile(member) as f:
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
            if h.hexdigest()!=digest:raise RuntimeError('Extracted archive hash differs: '+relative)
    if checked!={'evidence/'+p for p in actual}:raise RuntimeError('Archive is incomplete')
    final=receipt_dir/'s2-evidence.tar.gz'
    with archive.open('rb') as source,final.open('xb') as target:shutil.copyfileobj(source,target)
    if sha(final)!=expected:raise RuntimeError('Final WORK archive differs')
    with (receipt_dir/'s2-evidence.tar.gz.sha256').open('x') as f:f.write(expected+'  '+final.name+'\n')
    receipt=dict(job_id=job,archive=str(final),sha256=expected,manifest_files_verified=len(manifest),
        collector_unchanged=True,selection_unchanged=True,new_builds=0,new_simulations=0,
        original_records_modified=False,design_snapshot_sha256=sha(design),
        source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(receipt_dir/'return.json',receipt);save(out/'final.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
