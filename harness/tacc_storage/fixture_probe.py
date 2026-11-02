#!/usr/bin/env python3
"""Container probe for the replay storage check; never runs firmware.

Uses the replay mounts, repeats replay_worker.py's read-only precondition checks
for this slot's share of the roster, imports (does not call) the frozen worker,
then appends to new SCRATCH output until the coordinator stops it.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--proposal', type=Path, required=True)
    ap.add_argument('--slot', type=int, required=True)
    ap.add_argument('--slots', type=int, required=True)
    ap.add_argument('--seconds', type=int, required=True)
    a = ap.parse_args()
    if sha(a.proposal) != os.environ['RTC_REPLAY_PROPOSAL_SHA256']:
        raise RuntimeError('Replay proposal differs')
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
    rel = plan['output_relative']
    out = bundle / rel
    # Mount flags are read without attempting a write to any original path.
    wanted = {'/primary': True, '/bundle': True, str(out / 'builds'): True, '/renode': True,
              '/sealed-s2': True, '/replay': True, '/replay-proposal.json': True,
              str(out): False, '/tmp': False, '/var/tmp': False, os.environ['HOME']: False}
    flags = {p: bool(os.statvfs(p).f_flag & os.ST_RDONLY) for p in wanted}
    if flags != wanted:
        raise RuntimeError('Mount flags differ: ' + repr(flags))
    for kind in ('records', 'uart', 'monitor', 'traces', 'platforms'):
        if (out / kind).exists():
            raise RuntimeError('New output already holds scientific output: ' + kind)
    original_out = primary_root / rel
    checked = []
    for selected in proposal['tasks'][a.slot::a.slots]:
        index = selected['primary_task']['index']
        task = next(t for t in plan['tasks'] if t['index'] == index)
        if task != selected['primary_task']:
            raise RuntimeError('Replay task differs from the original')
        rid = selected['primary_run_id']
        source_record = original_out / 'records' / (rid + '.json')
        if sha(source_record) != selected['primary_record_sha256']:
            raise RuntimeError('Original primary record differs')
        original = json.loads(source_record.read_text())
        if original['cases'] != selected['primary_case_vector']:
            raise RuntimeError('Original case vector differs')
        if sha(original_out / 'traces' / (rid + '.json')) != selected['primary_trace_sha256']:
            raise RuntimeError('Original primary trace differs')
        build = out / 'builds' / task['unit_id'] / 'build_record.json'
        record = json.loads(build.read_text())
        if sha(build) != original['build_record_sha256']:
            raise RuntimeError('Original build record differs')
        if sha(bundle / record['elf_path']) != original['elf_sha256']:
            raise RuntimeError('Original ELF differs')
        checked.append(index)
    frozen = Path('/sealed-s2/worker.py')
    if sha(frozen) != proposal['unchanged_simulation_worker_sha256']:
        raise RuntimeError('Frozen simulation implementation differs')
    spec = importlib.util.spec_from_file_location('frozen_s2_replay', frozen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.insert(0, '/opt/rtc-code/harness/phase0')
    from session import RenodeSession
    binary = Path(os.environ.get('RENODE_BIN', '/opt/renode/renode-pinned'))
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    if version != plan['renode_version'] or not callable(module.run) or not RenodeSession:
        raise RuntimeError('Calibrated Renode/runtime differs')
    Path('/tmp/fixture-marker').write_text(str(a.slot) + '\n')
    report = out / 'fixture'
    report.mkdir(parents=True, exist_ok=True)
    with (report / f'probe-{a.slot}.json').open('x') as stream:
        json.dump(dict(slot=a.slot, checked_indices=checked, mount_read_only=flags,
                       renode_version=version, firmware_runs=0, worker_run_called=False,
                       node=os.environ['RTC_NODE_NAME'], slurm_job_id=os.environ['SLURM_JOB_ID']),
                  stream, indent=2, sort_keys=True)
        stream.write('\n')
    with (report / f'writer-{a.slot}.log').open('x') as stream:
        for tick in range(a.seconds):
            stream.write(f'{tick} {time.time()}\n')
            stream.flush()
            time.sleep(1)


if __name__ == '__main__':
    main()
