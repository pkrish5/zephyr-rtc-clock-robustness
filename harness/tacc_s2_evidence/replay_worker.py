#!/usr/bin/env python3
"""New provenance adapter calling the frozen S2 simulation function unchanged.

Not an execution authorization. The original bundle and records are mounted
read only at /primary, identical inputs at /bundle, and only /bundle's result
output is overlaid with new SCRATCH storage (build records separately read only).
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--proposal', type=Path, required=True)
    ap.add_argument('--index', type=int, required=True)
    a = ap.parse_args()
    # Proposal identity is supplied by the sealed outer job manifest; the
    # proposal itself remains deliberately marked unapproved until submission.
    if sha(a.proposal) != os.environ['RTC_REPLAY_PROPOSAL_SHA256']:
        raise RuntimeError('Replay proposal differs')
    if os.environ['SLURM_JOB_PARTITION'] != 'normal':
        raise RuntimeError('Scientific replay requires its approved normal allocation')
    proposal = json.loads(a.proposal.read_text())
    primary_root, bundle = Path('/primary'), Path('/bundle')
    plan = json.loads((bundle / 'plan.json').read_text())
    if sha(bundle / 'plan.json') != proposal['source_primary_plan_sha256']:
        raise RuntimeError('Primary plan differs')
    if sha(bundle / 'plan.json') != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Primary plan seal differs')
    if os.environ['RTC_CONTAINER_SHA256'] != plan['image_sha256']:
        raise RuntimeError('Calibrated image identity differs')
    for rel, expected in plan['input_sha256'].items():
        if sha(bundle / rel) != expected:
            raise RuntimeError('Original input differs: ' + rel)
    selected = [t for t in proposal['tasks'] if t['primary_task']['index'] == a.index]
    if len(selected) != 1:
        raise RuntimeError('Index is not uniquely registered for replay')
    selected = selected[0]
    task = next(t for t in plan['tasks'] if t['index'] == a.index)
    if task != selected['primary_task']:
        raise RuntimeError('Replay task differs from the original')
    original_out = primary_root / plan['output_relative']
    rid = selected['primary_run_id']
    source_record = original_out / 'records' / (rid + '.json')
    if sha(source_record) != selected['primary_record_sha256']:
        raise RuntimeError('Original primary record differs')
    original = json.loads(source_record.read_text())
    if original['cases'] != selected['primary_case_vector']:
        raise RuntimeError('Original case vector differs')
    if sha(original_out / 'traces' / (rid + '.json')) != selected['primary_trace_sha256']:
        raise RuntimeError('Original primary trace differs')
    # The mount must expose the original build record and ELF, never a rebuild.
    build = bundle / plan['output_relative'] / 'builds' / task['unit_id'] / 'build_record.json'
    record = json.loads(build.read_text())
    if sha(build) != original['build_record_sha256']:
        raise RuntimeError('Original build record differs')
    if sha(bundle / record['elf_path']) != original['elf_sha256']:
        raise RuntimeError('Original ELF differs')
    frozen = Path('/sealed-s2/worker.py')
    if sha(frozen) != proposal['unchanged_simulation_worker_sha256']:
        raise RuntimeError('Frozen simulation implementation differs')
    spec = importlib.util.spec_from_file_location('frozen_s2_replay', frozen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Identical task, plan, logical paths and simulation body; real new Slurm
    # node/job/partition metadata flows through its existing provenance call.
    module.run(bundle, plan, task)


if __name__ == '__main__':
    main()
