#!/usr/bin/env python3
"""New S2 reference adapter; reuse frozen build/run bodies without changing them."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def read(path):
    return json.loads(path.read_text())


def check_plan(bundle):
    path = bundle / 'plan.json'
    if sha(path) != os.environ['RTC_REFERENCE_PLAN_SHA256'] or sha(path) != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Reference plan seal differs')
    plan = read(path)
    if os.environ['RTC_CONTAINER_SHA256'] != plan['image_sha256']:
        raise RuntimeError('Calibrated image differs')
    for rel, expected in plan['input_sha256'].items():
        if sha(bundle / rel) != expected:
            raise RuntimeError('Reference input changed: ' + rel)
    return plan


def setup():
    repo = Path(os.environ['RTC_REPO']).resolve()
    packet = Path(os.environ['RTC_REFERENCE_PACKET']).resolve()
    primary = Path(os.environ['RTC_PRIMARY_BUNDLE']).resolve()
    base = Path(os.environ['RTC_JOB_BASE']).resolve()
    out = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    packet.relative_to(repo)
    primary.relative_to(repo / 'tacc_work')
    code_path = packet / 'code.sha256.json'
    if sha(code_path) != os.environ['RTC_REFERENCE_CODE_SHA256']:
        raise RuntimeError('Reference code manifest differs')
    code = read(code_path)
    for rel, value in code.items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts or sha(repo / rel) != value:
            raise RuntimeError('Reference execution code differs: ' + rel)
    source = packet / 'plan.json'
    if sha(source) != os.environ['RTC_REFERENCE_PLAN_SHA256']:
        raise RuntimeError('Reference packet plan differs')
    plan = read(source)
    if sha(primary / 'plan.json') != plan['source_primary_plan_sha256']:
        raise RuntimeError('Original S2 plan differs')
    if sha(Path(os.environ['RTC_IMAGE'])) != plan['image_sha256']:
        raise RuntimeError('Container bytes differ')
    bundle = base / 'reference-bundle'
    bundle.mkdir(exist_ok=False)
    for rel, value in plan['input_sha256'].items():
        src = packet / 'inputs' / rel
        if not src.exists():
            src = primary / rel
        if sha(src) != value:
            raise RuntimeError('Staged reference input differs: ' + rel)
        target = bundle / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        if sha(target) != value:
            raise RuntimeError('Reference input copy differs')
    shutil.copyfile(source, bundle / 'plan.json')
    shutil.copyfile(packet / 'plan.sha256', bundle / 'plan.sha256')
    # Scratch only. Logical bundle/output is overlaid with the packed output.
    (bundle / plan['output_relative']).mkdir(parents=True)
    for phase in ('qualification', 'evaluation'):
        jobfile = out / 'launcher' / phase / 'jobfile'
        jobfile.parent.mkdir(parents=True, exist_ok=True)
        with jobfile.open('x') as stream:
            for task in plan['tasks']:
                if task['phase'] == phase:
                    stream.write(shlex.join(['bash', '-l', str(repo / 'harness/tacc_s2_references/task.sh'),
                                             'run', str(task['index'])]) + '\n')
    save(out / 'job_metadata/setup.json', dict(plan_sha256=sha(source), code_manifest_sha256=sha(code_path),
        original_primary_plan_sha256=plan['source_primary_plan_sha256'],
        new_bundle=str(bundle), original_bundle=str(primary), original_records_modified=False,
        reference_units=len(plan['units']), qualification_launches=sum(t['phase'] == 'qualification' for t in plan['tasks']),
        evaluation_launches=sum(t['phase'] == 'evaluation' for t in plan['tasks']),
        full_application_case_failures_covered=plan['primary_failure_slots_covered'],
        board_roles=plan['board_roles']))


def frozen_worker(plan):
    source = Path('/sealed-s2/worker.py')
    if sha(source) != plan['frozen_s2_worker_sha256']:
        raise RuntimeError('Original build/run implementation differs')
    spec = importlib.util.spec_from_file_location('frozen_s2_reference_worker', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(bundle, plan, unit_id):
    unit = next(u for u in plan['units'] if u['id'] == unit_id)
    for rel, expected in plan['reference_sources_sha256'].items():
        if sha(Path('/reference-app') / rel) != expected:
            raise RuntimeError('Reference source changed: ' + rel)
    module = frozen_worker(plan)
    module.build(bundle, plan, unit)
    out = bundle / plan['output_relative'] / 'builds' / unit_id
    record = read(out / 'build_record.json')
    if record['status'] != 'built':
        raise RuntimeError('Reference build failed: ' + unit_id)
    tree = out / 'build'
    keep = dict(record['build_products_sha256'])
    keep['zephyr/zephyr.elf'] = record['elf_sha256']
    for rel, expected in keep.items():
        if sha(tree / rel) != expected:
            raise RuntimeError('New reference build product changed')
        retained = out / 'kept_products' / rel
        retained.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tree / rel, retained)
        if sha(retained) != expected:
            raise RuntimeError('Pre-move kept reference build product changed')
    intermediate = Path('/scratch-builds') / unit_id
    if intermediate.exists():
        raise RuntimeError('Refusing to reuse an intermediate build path')
    # These are different container bind mounts, even on the same host FS.
    # move() safely handles EXDEV without following source-tree symlinks.
    shutil.move(str(tree), str(intermediate))
    for rel, expected in keep.items():
        target = tree / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out / 'kept_products' / rel, target)
        if sha(target) != expected:
            raise RuntimeError('Kept reference build product changed')
    save(out / 'retention.json', dict(kept_sha256=keep, intermediates_moved_to=str(intermediate),
                                     intermediates_deleted=False, original_elves_changed=False))


def run(bundle, plan, index):
    task = next(t for t in plan['tasks'] if t['index'] == index)
    frozen_worker(plan).run(bundle, plan, task)


def audit_phase(phase):
    base = Path(os.environ['RTC_JOB_BASE']).resolve()
    out = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    bundle = base / 'reference-bundle'
    plan = check_plan(bundle)
    rows, errors = [], []
    for task in plan['tasks']:
        if task['phase'] != phase:
            continue
        unit = next(u for u in plan['units'] if u['id'] == task['unit_id'])
        rid = f"{unit['id']}-{task['condition']}-{task['index']:03d}"
        p = out / 'records' / (rid + '.json')
        row = dict(index=task['index'], run_id=rid, unit_id=unit['id'], board_role=plan['board_roles'][unit['board_id']],
                   frequency_hz=task['frequency_hz'], primary_run_id=task.get('primary_run_id'), status='missing',
                   linked_primary_cases=task.get('failed_cases', []))
        if p.exists():
            r = read(p)
            row.update(record_sha256=sha(p), cases=r['cases'], error=r['error'], status='complete' if r['application_completed'] else 'incomplete')
            if r['error'] or not r['application_completed'] or r['missing_cases'] or r['duplicate_cases']:
                errors.append(dict(index=task['index'], error='Missing or invalid reference verdict'))
            if str(r['slurm_job_id']) != os.environ['SLURM_JOB_ID'] or r['container_sha256'] != plan['image_sha256']:
                errors.append(dict(index=task['index'], error='Reference provenance differs'))
            for kind, expected in r['log_sha256'].items():
                suffix = '.json' if kind == 'traces' else '.log'
                raw = out / kind / (rid + suffix)
                if expected and (not raw.exists() or sha(raw) != expected):
                    errors.append(dict(index=task['index'], error='Reference raw evidence hash differs: ' + kind))
            for c in r['cases']:
                if phase == 'qualification':
                    # A retained rate contract can fail at a legal endpoint;
                    # it never licenses a brittle-test label.
                    rate = c['case'] == 'ref_seconds.test_a_rate_contract'
                    allowed = ('pass', 'fail') if rate and task['condition'] != 'nominal' else ('pass',)
                    if c['status'] not in allowed:
                        errors.append(dict(index=task['index'], case=c['case'], outcome=c['status'],
                                           flag='firmware_or_simulator_reference_failure_not_brittleness'))
        else:
            errors.append(dict(index=task['index'], error='Reference record absent'))
        rows.append(row)
    save(out / 'audits' / (phase + '.json'), dict(phase=phase, launches=len(rows), rows=rows,
        errors=errors, valid=not errors, board_roles=plan['board_roles'],
        original_records_modified=False, slurm_job_id=os.environ['SLURM_JOB_ID']))
    if errors:
        raise RuntimeError('Reference phase has anomalies; preserve archive and stop: ' + repr(errors[:3]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=('setup', 'build', 'run', 'audit-qualification', 'audit-evaluation'))
    ap.add_argument('--unit')
    ap.add_argument('--index', type=int)
    a = ap.parse_args()
    if a.mode == 'setup':
        setup()
    elif a.mode.startswith('audit-'):
        audit_phase(a.mode.split('-', 1)[1])
    else:
        bundle = Path('/bundle')
        plan = check_plan(bundle)
        build(bundle, plan, a.unit) if a.mode == 'build' else run(bundle, plan, a.index)


if __name__ == '__main__':
    main()
