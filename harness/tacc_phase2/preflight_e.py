#!/usr/bin/env python3
"""Compute-node preflight for each approved E stage and the D prerequisite."""
import argparse
import math
import os
from pathlib import Path
from support import IMAGE_SHA, read, save, sha, utc, verify_inputs

ap=argparse.ArgumentParser()
ap.add_argument('--bundle',type=Path,required=True)
ap.add_argument('--repo',type=Path,required=True)
ap.add_argument('--image',type=Path,required=True)
ap.add_argument('--stage',choices=['gates','evaluate'],required=True)
ap.add_argument('--d-bundle',type=Path,required=True)
a=ap.parse_args()
if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Compute allocation required')
p=verify_inputs(a.bundle,a.repo)
if sha(a.image)!=IMAGE_SHA:raise RuntimeError('Image differs from calibration')
out=a.bundle/'study'/p['output_relative']
if (out/'STOP.json').exists():raise RuntimeError('Study STOP exists')
if a.stage=='gates':
    dp=verify_inputs(a.d_bundle,a.repo)
    dout=a.d_bundle/'study'/dp['output_relative']
    report=read(dout/'report.json')
    if report.get('stop_marker') or report.get('outcomes')!={'pass':216} or report.get('build_outcomes')!={'pass':216} or not report.get('complete'):
        raise RuntimeError('D prerequisite is not 216 passing disabled controls: '+str(report.get('outcomes')))
    for path in (dout/'records').glob('*.json'):
        r=read(path)
        for key in ('trace','uart','monitor'):
            if r.get(key+'_sha256') and sha(a.d_bundle/'study'/r[key+'_path'])!=r[key+'_sha256']:
                raise RuntimeError('D raw output differs')
    save(out/'d_prerequisite.json',dict(timestamp_utc=utc(),report_sha256=sha(dout/'report.json'),
         outcomes=report['outcomes'],build_outcomes=report['build_outcomes'],validated=True))
else:
    if not read(out/'d_prerequisite.json')['validated']:raise RuntimeError('D prerequisite absent')
    if sha(out/'execution.json')!=(out/'execution.sha256').read_text().split()[0]:
        raise RuntimeError('Generated ELF manifest seal differs')
mem={k:int(v.strip().split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
     if k in ('MemTotal','MemAvailable')}
available=mem['MemAvailable']
for name in ('/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory/memory.limit_in_bytes'):
    f=Path(name)
    if f.exists() and f.read_text().strip().isdigit():available=min(available,int(f.read_text().strip())//1024)
per_worker=4*1024**2 if a.stage=='gates' else 1.5*320488
cap=16 if a.stage=='gates' else 32
n=min(cap,len(os.sched_getaffinity(0)),math.floor(.8*available/per_worker))
if n<1:raise RuntimeError('Insufficient memory')
save(out/f'capacity-{a.stage}.json',dict(concurrency=n,available_kib=available,per_worker_allowance_kib=per_worker,
    memory_fraction_ceiling=.8,container_sha256=IMAGE_SHA,slurm_job_id=os.environ['SLURM_JOB_ID']))
print(a.stage,'preflight passed; concurrency',n)
