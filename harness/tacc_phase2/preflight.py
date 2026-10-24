#!/usr/bin/env python3
import argparse
import math
import os
from pathlib import Path
from support import IMAGE_SHA, save, sha, verify_inputs

ap = argparse.ArgumentParser()
ap.add_argument('--bundle', type=Path, required=True)
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--image', type=Path, required=True)
ap.add_argument('--cap', type=int, required=True)
a = ap.parse_args()
p = verify_inputs(a.bundle, a.repo)
if not os.environ.get('SLURM_JOB_ID'):
    raise RuntimeError('Compute allocation required')
if sha(a.image) != IMAGE_SHA:
    raise RuntimeError('Image differs')
mem = {k: int(v.strip().split()[0]) for k, v in
       (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
       if k in ('MemTotal', 'MemAvailable')}
available = mem['MemAvailable']
for name in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
    f = Path(name)
    if f.exists() and f.read_text().strip().isdigit():
        available = min(available, int(f.read_text().strip()) // 1024)
# Measured Phase 1 peak with 50% headroom; D additionally reserves 4 GiB/build.
per_worker = 1.5 * 320488 if p['phase'] == 'AB' else 4 * 1024**2
n = min(a.cap, len(os.sched_getaffinity(0)), math.floor(.8 * available / per_worker))
if n < 1:
    raise RuntimeError('Insufficient memory')
save(a.bundle / 'study' / p['output_relative'] / 'capacity.json',
     dict(concurrency=n, memory_available_kib=available, per_worker_allowance_kib=per_worker,
          memory_fraction_ceiling=.8, node_cpus=len(os.sched_getaffinity(0)), image_sha256=IMAGE_SHA))
print(n)
