#!/usr/bin/env python3
"""New diagnostic adapter, importing frozen scientific function bodies."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def main():
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['build','reference','replay'])
    p.add_argument('--unit'); p.add_argument('--index', type=int); a = p.parse_args()
    assert os.environ['SLURM_JOB_PARTITION'] == 'development'
    assert os.environ['SLURM_JOB_ACCOUNT'].upper() == 'CCR26073'
    packet = Path('/repo/notes/counter_verification_2026-11-11_v1/packet')
    ep = packet / 'execution.json'; assert sha(ep) == os.environ['RTC_VERIFY_EXECUTION_SHA256']
    e = json.loads(ep.read_text())
    for rel, digest in e['code_sha256'].items(): assert sha(Path('/repo') / rel) == digest, rel
    assert sha(Path('/sealed-s2/worker.py')) == e['frozen_s2_worker_sha256']
    bundle = Path('/bundle')
    if a.mode == 'replay':
        assert sha(bundle / 'plan.json') == e['original_counter_plan_sha256']
        plan = json.loads((bundle / 'plan.json').read_text())
        for rel, digest in plan['input_sha256'].items(): assert sha(bundle / rel) == digest, rel
        for rel, digest in plan['code_sha256'].items(): assert sha(Path('/repo') / rel) == digest, rel
        selected = e['selection']['replays'][a.index]
        task = plan['tasks'][selected['original_task_index']]
        assert task == selected['original_task']
        plan_elf = bundle / e['original_builds'][task['unit_id']]['elf_path']
        assert sha(plan_elf) == selected['elf_sha256']
        load('frozen_s2_worker', Path('/sealed-s2/worker.py')).run(bundle, plan, task)
    else:
        driver = load('frozen_reference_adapter', Path('/reference-adapter/driver.py'))
        plan = driver.check_plan(bundle)
        if a.mode == 'build': driver.build(bundle, plan, a.unit)
        else: driver.run(bundle, plan, a.index)

if __name__ == '__main__': main()
