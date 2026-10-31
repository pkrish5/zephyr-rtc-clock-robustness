#!/usr/bin/env python3
"""Read-only compute-node check of the original 30,067 protected files."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path

BASELINE_SHA = 'b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    if os.environ['SLURM_JOB_PARTITION'] not in ('development', 'normal'):
        raise RuntimeError('Compute allocation required')
    repo = Path(os.environ['RTC_REPO']).resolve()
    repo.relative_to(Path(os.environ['WORK']).resolve())
    a.out.resolve().relative_to(Path(os.environ['RTC_JOB_BASE']).resolve())
    baseline = repo / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline) != BASELINE_SHA:
        raise RuntimeError('Original protection ledger differs')
    original = json.loads(baseline.read_text())['hashes']
    if len(original) != 30067:
        raise RuntimeError('Protection roster differs')
    def check(item):
        rel, expected = item
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise RuntimeError('Unsafe protected path')
        return rel, dict(before_sha256=expected, after_sha256=sha(repo / rel))
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = dict(pool.map(check, original.items()))
    changed = [rel for rel, row in rows.items()
               if row['before_sha256'] != row['after_sha256']]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x') as stream:
        json.dump(dict(count=len(rows), changed=changed, files=rows,
                       baseline_sha256=BASELINE_SHA,
                       slurm_job_id=os.environ['SLURM_JOB_ID']), stream, sort_keys=True)
        stream.write('\n')
    if changed:
        raise RuntimeError('Protected files differ: ' + repr(changed))


if __name__ == '__main__':
    main()
