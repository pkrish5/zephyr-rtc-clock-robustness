#!/usr/bin/env python3
"""Compute-node audit/archive of S2 evidence; no build or firmware execution."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--previous',type=Path,required=True)
    ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--dest',type=Path,required=True)
    ap.add_argument('--slurm-logs',type=Path,required=True)
    a=ap.parse_args()
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development compute node only')
    repo=Path(os.environ['RTC_REPO']).resolve()
    for p in (a.bundle,a.previous,a.runtime,a.dest,a.slurm_logs):p.resolve().relative_to(repo)
    plan=json.loads((a.bundle/'plan.json').read_text())
    if sha(a.bundle/'plan.json')!=(a.bundle/'plan.sha256').read_text().split()[0]:raise RuntimeError('Plan seal differs')
    out=a.bundle/plan['output_relative']
    a.dest.mkdir(parents=True,exist_ok=False)
    for rel,digest in plan['input_sha256'].items():
        if sha(a.bundle/rel)!=digest:raise RuntimeError('Bundle input differs: '+rel)
    for rel,digest in plan['code_sha256'].items():
        src=repo/rel
        if sha(src)!=digest:raise RuntimeError('Sealed S2 code differs: '+rel)
        target=a.dest/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    design=repo/'paper/DESIGN.md'
    if sha(design)!=plan['design_sha256']:raise RuntimeError('Registered design differs')
    shutil.copyfile(design,a.dest/'DESIGN.md')
    rows=[]
    for p in sorted((out/'records').glob('*.json')):
        r=json.loads(p.read_text())
        for kind,digest in r.get('log_sha256',{}).items():
            if digest:
                q=out/kind/(r['run_id']+('.json' if kind=='traces' else '.log'))
                if sha(q)!=digest:raise RuntimeError('Run artifact differs: '+str(q))
        rows.append(r)
    builds=[]
    for u in plan['units']:
        base=out/'builds'/u['id'];record=json.loads((base/'build_record.json').read_text())
        if sha(base/'build.log')!=record['log_sha256']:raise RuntimeError('Build log differs')
        if record.get('elf_path') and sha(a.bundle/record['elf_path'])!=record['elf_sha256']:raise RuntimeError('ELF differs')
        for rel,digest in record['build_products_sha256'].items():
            if sha(base/'build'/rel)!=digest:raise RuntimeError('Build product differs')
        builds.append(dict(unit_id=u['id'],status=record['status'],elf_sha256=record.get('elf_sha256')))
    inventory=[];dedup=a.dest/'runtime-cache-blobs';dedup.mkdir()
    for r in rows:
        matches=list(a.runtime.glob(f"{r['slurm_job_id']}-run-{r['index']}.*"))
        if len(matches)!=1:raise RuntimeError('Runtime directory is missing or ambiguous: '+r['run_id'])
        cache=matches[0]/'home/.config/renode'
        files=[]
        for f in sorted(cache.rglob('*')):
            if not f.is_file():continue
            f.resolve().relative_to(cache.resolve())
            digest=sha(f);dst=dedup/digest
            if not dst.exists():shutil.copyfile(f,dst)
            entry=dict(relative_path=str(f.relative_to(cache)),sha256=digest,size_bytes=f.stat().st_size)
            if f.name=='binaries_index':
                entry['indexed_public_urls']=[x.decode('ascii') for x in re.findall(rb'https?://[A-Za-z0-9_./?=&%+~:#-]+',f.read_bytes())]
            files.append(entry)
        inventory.append(dict(run_id=r['run_id'],job_id=r['slurm_job_id'],task_index=r['index'],files=files))
    save(a.dest/'runtime-cache-inventory.json',inventory)
    # Snapshot only after the qualification job has stopped. No source tree mutation.
    shutil.copytree(out,a.dest/'raw')
    shutil.copytree(a.slurm_logs,a.dest/'slurm')
    for rel in ['plan.json','plan.sha256','approved_runtime.json']:
        shutil.copyfile(a.bundle/rel,a.dest/rel)
    for rel in ['configs','renode','renode-cache']:
        shutil.copytree(a.bundle/rel,a.dest/rel)
    oldplan=json.loads((a.previous/'plan.json').read_text());oldout=a.previous/oldplan['output_relative']
    first=a.dest/'first-attempt';first.mkdir()
    for rel in ['plan.json','plan.sha256']:shutil.copyfile(a.previous/rel,first/rel)
    for u in oldplan['units']:
        for name in ['build_record.json','build.log']:
            p=oldout/'builds'/u['id']/name;dst=first/'builds'/u['id']/name
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    for name in ['stdout','processes','resources','platforms']:
        p=oldout/name
        if p.exists():shutil.copytree(p,first/name)
    # Run the sealed reporter against a new snapshot only. Never resume tests or
    # write derived analyses into the original qualification output directory.
    snapshot_out=a.dest/plan['output_relative']
    snapshot_out.parent.mkdir(parents=True,exist_ok=True)
    snapshot_out.symlink_to(a.dest.resolve()/'raw')
    report_process=subprocess.run([sys.executable,str(repo/'harness/tacc_s2/control.py'),
        'report','--bundle',str(a.dest)],capture_output=True,text=True)
    save(a.dest/'reporter_execution.json',dict(exit_code=report_process.returncode,
        stdout=report_process.stdout,stderr=report_process.stderr,
        original_qualification_output_modified=False))
    snapshot_out.unlink()
    report=a.dest/'raw/qualification_report.json'
    missing=sorted(set(t['index'] for t in plan['tasks'])-set(r['index'] for r in rows))
    save(a.dest/'verification.json',dict(records_verified=len(rows),builds=builds,missing_task_indices=missing,
        report_present=report.exists(),plan_sha256=sha(a.bundle/'plan.json'),
        cache_runs=len(inventory),unique_cache_blobs=len(list(dedup.iterdir())),
        collector_sha256=sha(__file__),collector_job=os.environ['SLURM_JOB_ID'],
        new_firmware_runs=0,new_builds=0,production_authorized=False))
    manifest={str(p.relative_to(a.dest)):sha(p) for p in sorted(a.dest.rglob('*')) if p.is_file()}
    save(a.dest/'files.sha256.json',manifest)
    archive=a.dest.with_suffix('.tar.gz')
    if archive.exists():raise RuntimeError('Archive already exists')
    with tarfile.open(archive,'w:gz') as t:t.add(a.dest,arcname=a.dest.name)
    with archive.with_suffix(archive.suffix+'.sha256').open('x') as f:f.write(sha(archive)+'  '+archive.name+'\n')
    print(json.dumps(dict(archive=str(archive),sha256=sha(archive),records=len(rows),missing=missing)))


if __name__=='__main__':main()
