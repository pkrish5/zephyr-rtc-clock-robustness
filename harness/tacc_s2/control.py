#!/usr/bin/env python3
"""Compute-node preflight, packing and qualification report. Never submits jobs."""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import shlex
import shutil
from pathlib import Path


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')


def load(bundle):
    plan = json.loads((bundle / 'plan.json').read_text())
    if sha(bundle / 'plan.json') != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Plan changed')
    return plan, bundle / plan['output_relative']


def parse_rss(path):
    text = path.read_text()
    m = re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)', text)
    if not m:
        raise RuntimeError('No GNU time peak RSS: ' + str(path))
    return int(m.group(1)) * 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['preflight', 'reuse_builds', 'jobfile', 'capacity', 'report'])
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--repo', type=Path)
    ap.add_argument('--image', type=Path)
    ap.add_argument('--phase', choices=['build', 'nominal', 'calibration'])
    ap.add_argument('--out', type=Path)
    ap.add_argument('--previous', type=Path)
    a = ap.parse_args()
    plan, out = load(a.bundle)
    if a.command == 'preflight':
        if os.environ.get('SLURM_JOB_PARTITION') != 'development':
            raise RuntimeError('Development only; no production authorized')
        if sha(a.image) != plan['image_sha256']:
            raise RuntimeError('Image hash differs')
        for rel, digest in plan['code_sha256'].items():
            if sha(a.repo / rel) != digest:
                raise RuntimeError('Code differs: ' + rel)
        for rel, digest in plan['input_sha256'].items():
            if sha(a.bundle / rel) != digest:
                raise RuntimeError('Input differs: ' + rel)
        # Hash check the published source provenance, not only source file names.
        if sha(a.repo / 'paper/DESIGN.md') != plan['design_sha256']:
            raise RuntimeError('Registered design differs')
        out.mkdir(parents=True, exist_ok=True)
        save(out / ('preflight-' + os.environ['SLURM_JOB_ID'] + '.json'),
            dict(plan_sha256=sha(a.bundle / 'plan.json'), image_sha256=sha(a.image),
                inputs_verified=len(plan['input_sha256']), code_verified=len(plan['code_sha256']),
                slurm_job_id=os.environ['SLURM_JOB_ID'], production_authorized=False))
    elif a.command == 'reuse_builds':
        if os.environ.get('SLURM_JOB_PARTITION') != 'development':
            raise RuntimeError('Reuse audit must run on development compute node')
        a.previous.resolve().relative_to(Path(os.environ['RTC_REPO']).resolve())
        old, oldout = load(a.previous)
        for k in ('units', 'boards', 'tasks', 'upstream_input_sha256', 'original_platform_sha256', 'image_sha256', 'output_relative'):
            if old[k] != plan[k]:
                raise RuntimeError('Scientific configuration changed across packaging fix: ' + k)
        # All old inputs are still present and byte-identical; the new plan only adds
        # approved runtime provenance. The simulation worker is unchanged, too.
        if old['code_sha256']['harness/tacc_s2/worker.py'] != plan['code_sha256']['harness/tacc_s2/worker.py']:
            raise RuntimeError('Simulation/build worker changed')
        for rel, digest in old['input_sha256'].items():
            if plan['input_sha256'].get(rel) != digest or sha(a.bundle / rel) != digest:
                raise RuntimeError('Input differs across metadata fix: ' + rel)
        audit = []
        for unit in plan['units']:
            src = oldout / 'builds' / unit['id']
            dst = out / 'builds' / unit['id']
            record = json.loads((src / 'build_record.json').read_text())
            paths = ['build_record.json', 'build.log']
            if sha(src / 'build.log') != record['log_sha256']:
                raise RuntimeError('Old build log changed')
            for rel, digest in record['build_products_sha256'].items():
                if sha(src / 'build' / rel) != digest:
                    raise RuntimeError('Old generated build product changed')
                paths.append('build/' + rel)
            if record.get('elf_path'):
                elf = a.previous / record['elf_path']
                if sha(elf) != record['elf_sha256']:
                    raise RuntimeError('Old new-build ELF changed')
                paths.append(str(elf.relative_to(src)))
            dst.mkdir(parents=True, exist_ok=False)
            for rel in paths:
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src / rel, target)
                if sha(src / rel) != sha(target):
                    raise RuntimeError('Copied bytes differ')
            audit.append(dict(unit_id=unit['id'], original_build_job=record['slurm_job_id'],
                build_record_sha256=sha(src / 'build_record.json'), elf_sha256=record.get('elf_sha256'),
                copied_files=len(paths), byte_identical=True))
        save(out / 'reused_build_audit.json', dict(previous_plan_sha256=sha(a.previous / 'plan.json'),
            new_plan_sha256=sha(a.bundle / 'plan.json'), builds=audit,
            changed_scientific_inputs=[], worker_unchanged=True,
            cause='Use the already calibrated Linux build-date string, rather than the local macOS string'))
    elif a.command == 'jobfile':
        if a.phase == 'build':
            tasks = [('build', i) for i in range(len(plan['units']))]
        elif a.phase == 'nominal':
            tasks = [('run', t['index']) for t in plan['tasks']
                if t['condition'] == 'nominal' and t['index'] != plan['probe_task_index']]
        else:
            tasks = []
            for t in plan['tasks']:
                if t['condition'] == 'nominal':
                    continue
                ns = [n for n in plan['tasks'] if n['unit_id'] == t['unit_id'] and n['condition'] == 'nominal']
                baseline = []
                for n in ns:
                    rid = f"{n['unit_id']}-nominal-{n['index']:03d}"
                    p = out / 'records' / (rid + '.json')
                    baseline.append(json.loads(p.read_text()) if p.exists() else {})
                ready = len(baseline) == 5 and all(r.get('application_completed') and
                    not r.get('missing_cases') and not r.get('duplicate_cases') for r in baseline)
                if ready:
                    tasks.append(('run', t['index']))
                else:
                    rid = f"{t['unit_id']}-{t['condition']}-{t['index']:03d}"
                    save(out / 'not_attempted' / (rid + '.json'), dict(**t,
                        reason='five complete nominal application runs unavailable; no calibration launched'))
        with a.out.open('x') as f:
            for stage, index in tasks:
                f.write(shlex.join(['bash', '-l', str(a.repo / 'harness/tacc_s2/task.sh'), stage, str(index)]) + '\n')
    elif a.command == 'capacity':
        task = plan['tasks'][plan['probe_task_index']]
        rid = f"{task['unit_id']}-{task['condition']}-{task['index']:03d}"
        probe = json.loads((out / 'records' / (rid + '.json')).read_text())
        if probe['outcome'] != 'complete' or probe['missing_cases'] or probe['duplicate_cases']:
            raise RuntimeError('First resource probe did not complete all cases; stop packing and retain evidence')
        rss = parse_rss(out / 'resources/run' / (str(task['index']) + '.time'))
        mem = {k: int(v.split()[0]) * 1024 for k, v in re.findall(r'^(\w+):\s*(.*)$', Path('/proc/meminfo').read_text(), re.M)}
        workers = min(plan['maximum_workers'], len(os.sched_getaffinity(0)),
                      math.floor(0.8 * mem['MemAvailable'] / (1.5 * rss)))
        if workers < 1:
            raise RuntimeError('Memory budget allows no workers')
        save(out / 'capacity.json', dict(workers=workers, probe_peak_rss_bytes=rss,
            node_mem_available_bytes=mem['MemAvailable'], safety_multiplier=1.5, memory_fraction=0.8,
            first_probe_record=rid, first_probe_wall_seconds=probe['wall_seconds'],
            node_name=os.uname().nodename, slurm_job_id=os.environ['SLURM_JOB_ID'],
            warning='One application estimate; each remaining launch is also measured. Recost before production.'))
    else:
        records = [json.loads(p.read_text()) for p in sorted((out / 'records').glob('*.json'))]
        by_index = {r['index']: r for r in records}
        cases, units, watchdog = [], [], []
        for u in plan['units']:
            rows = [r for r in records if r['unit_id'] == u['id']]
            build_path = out / 'builds' / u['id'] / 'build_record.json'
            build = json.loads(build_path.read_text()) if build_path.exists() else dict(status='missing_build_record')
            if u['family'] == 'wdt':
                watchdog.append(dict(unit_id=u['id'], build_status=build['status'], attempt=plan['watchdog_attempt'],
                    qualified=any(r.get('watchdog_reboot_and_completion') for r in rows),
                    records=[r['run_id'] for r in rows], exclusion_if_failed='reboot and explicit completion not demonstrated'))
                continue
            nominal = [r for r in rows if r['condition'] == 'nominal']
            cal = [r for r in rows if r['condition'] != 'nominal']
            eligible = []
            for case in u['expected_declared_cases']:
                def status(r):
                    found = [c['status'] for c in r.get('cases', []) if c['case'] == case]
                    return found[0] if r.get('application_completed') and len(found) == 1 else 'missing'
                ns = [status(r) for r in nominal]
                classified = 'working' if len(ns) == 5 and all(s == 'pass' for s in ns) else (
                    'capability_skip' if len(ns) == 5 and all(s == 'skip' for s in ns) else
                    'build_failure' if build['status'] != 'built' else
                    'nominal_failure' if 'fail' in ns else
                    'mixed_skip' if 'skip' in ns else 'missing_nominal')
                if classified == 'working':
                    eligible.append(case)
                cases.append(dict(board=plan['boards'][u['board_id']]['board'], unit_id=u['id'], case=case,
                    nominal_classification=classified, nominal_pass=ns.count('pass'), nominal_skip=ns.count('skip'),
                    nominal_fail=ns.count('fail'), nominal_missing=5-len(ns)+ns.count('missing'),
                    calibration_pass=sum(status(r) == 'pass' for r in cal),
                    calibration_skip=sum(status(r) == 'skip' for r in cal),
                    calibration_fail=sum(status(r) == 'fail' for r in cal),
                    calibration_missing=7-len(cal)+sum(status(r) == 'missing' for r in cal)))
            samples = [r['wall_seconds'] for r in rows if 'wall_seconds' in r]
            rss_samples = []
            for r in rows:
                p = out / 'resources/run' / (str(r['index']) + '.time')
                if p.exists():
                    rss_samples.append(parse_rss(p))
            dividers = sorted({d for r in rows for d in r.get('rtc_divider_observations', []) if d > 1})
            expected_divider = (39936 if u['family'] != 'rtc' else 32000) if u['board_id'] == 'f072' else 32000
            dts_path = out / 'builds' / u['id'] / 'build/zephyr/zephyr.dts'
            dts = dts_path.read_text() if dts_path.exists() else ''
            nominal_complete = len(nominal) == 5 and all(r.get('application_completed') and
                not r.get('missing_cases') and not r.get('duplicate_cases') for r in nominal)
            calibration_complete = len(cal) == 7 and all(r.get('application_completed') and
                not r.get('missing_cases') and not r.get('duplicate_cases') for r in cal)
            all_case_records_present = all(c['nominal_missing'] == 0 and c['calibration_missing'] == 0
                for c in cases if c['unit_id'] == u['id'])
            configuration_ready = bool(eligible) and nominal_complete and calibration_complete and all_case_records_present and dividers == [expected_divider]
            # All generated DTS/.config and PRER reads are preserved; semantic source review
            # is still required before admitting F072 or any new board to production.
            units.append(dict(unit_id=u['id'], build_status=build['status'], nominal_launches=len(nominal),
                calibration_launches=len(cal), qualified_cases=eligible, declared_cases=len(u['expected_declared_cases']),
                all_nominal_applications_complete=nominal_complete,
                all_calibration_applications_complete=calibration_complete,
                configuration_ready_for_review=configuration_ready,
                observed_dividers=dividers, source_expected_divider=expected_divider,
                programmed_divider_matches=bool(dividers) and dividers == [expected_divider],
                generated_dts_sha256=sha(dts_path) if dts else None,
                max_wall_seconds=max(samples) if samples else None,
                mean_wall_seconds=sum(samples)/len(samples) if samples else None,
                max_peak_rss_bytes=max(rss_samples) if rss_samples else None,
                provisional_production_launches=102 if configuration_ready else 0))
        with (out / 'per_case_qualification.csv').open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(cases[0]));writer.writeheader();writer.writerows(cases)
        capacity = json.loads((out / 'capacity.json').read_text())
        contributing = [u for u in units if u['configuration_ready_for_review'] and u['max_wall_seconds'] is not None]
        rough_su = sum(102*u['max_wall_seconds'] for u in contributing) / capacity['workers'] / 3600 * 1.5
        missing_tasks = [t['index'] for t in plan['tasks'] if t['index'] not in by_index]
        save(out / 'qualification_report.json', dict(units=units, watchdog=watchdog,
            scheduled_launches=len(plan['tasks']), recorded_launches=len(records), missing_task_indices=missing_tasks,
            per_case_csv_sha256=sha(out / 'per_case_qualification.csv'),
            provisional_primary_production_launches=sum(u['provisional_production_launches'] for u in units),
            provisional_primary_su=rough_su, costing='max measured full-application wall time *102 /workers /3600 *1.5; replay/reference reserves and build inclusion need final review',
            production_authorized=False, stop='STOP for user review. No normal job submitted. E/E2 unchanged.'))
        print('Qualification report written; STOP before production.')


if __name__ == '__main__':
    main()
