#!/usr/bin/env python3
"""Compute-only setup, qualified replay/reference phases, append-only accounting."""
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def read(p): return json.loads(p.read_text())
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(obj, f, indent=2, sort_keys=True); f.write('\n')

def main():
    assert os.environ['SLURM_JOB_PARTITION'] == 'development'
    assert os.environ['SLURM_JOB_ACCOUNT'].upper() == 'CCR26073'
    repo = Path(os.environ['RTC_REPO']); packet = Path(os.environ['RTC_VERIFY_PACKET'])
    out = Path(os.environ['RTC_JOB_OUTPUT']); base = Path(os.environ['RTC_JOB_BASE'])
    original = Path(os.environ['RTC_COUNTER_BUNDLE']); image = Path(os.environ['RTC_IMAGE'])
    ep = packet / 'execution.json'; e = read(ep)
    assert sha(ep) == (packet / 'execution.sha256').read_text().split()[0]
    assert sha(original / 'plan.json') == e['original_counter_plan_sha256']
    old = read(original / 'plan.json'); reference = read(packet / 'reference_plan.json')
    assert sha(packet / 'reference_plan.json') == e['reference_plan_sha256']
    assert sha(packet.parent / 'selection.json') == e['selection_sha256']
    assert sha(packet.parent / 'PROTOCOL.md') == e['protocol_sha256']
    assert sha(image) == e['image_sha256']
    env = dict(os.environ, RTC_REFERENCE_BUNDLE=str(base / 'reference-bundle'),
               RTC_REPLAY_OUT_REL=old['output_relative'], RTC_REFERENCE_OUT_REL=reference['output_relative'],
               RTC_REFERENCE_PLAN_SHA256=e['reference_plan_sha256'], RTC_VERIFY_EXECUTION_SHA256=sha(ep))
    copied_elves = {}
    phases_started = []; phase_exit_codes = {}; replay_results = []

    def guard():
        for rel, digest in e['code_sha256'].items(): assert sha(repo / rel) == digest, rel
        for rel, digest in e['reference_source_sha256'].items(): assert sha(repo / rel) == digest, rel
        for rel, digest in e['active_counter_inputs_sha256'].items(): assert sha(repo / rel) == digest, rel
        for unit, info in e['original_builds'].items():
            assert sha(original / info['elf_path']) == info['elf_sha256'], unit
            assert sha(original / old['output_relative'] / 'builds' / unit / 'build_record.json') == info['build_record_sha256'], unit
        for p, digest in copied_elves.items(): assert sha(p) == digest, str(p)

    guard()
    save(out / 'job_metadata/input_verification_before.json', dict(all_passed=True,
         active_counter_seals=764, execution_sha256=sha(ep), image_sha256=e['image_sha256'],
         original_elves_unchanged=4, account=os.environ['SLURM_JOB_ACCOUNT']))
    for p in [ep, packet / 'reference_plan.json', packet.parent / 'selection.json', packet.parent / 'PROTOCOL.md', packet.parent / 'COST.json']:
        shutil.copyfile(p, out / 'job_metadata' / p.name)
    new_bundle = base / 'reference-bundle'; new_bundle.mkdir()
    for rel, digest in reference['input_sha256'].items():
        source = original / rel; assert sha(source) == digest, rel
        target = new_bundle / rel; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target); assert sha(target) == digest
    shutil.copyfile(packet / 'reference_plan.json', new_bundle / 'plan.json')
    (new_bundle / 'plan.sha256').write_text(e['reference_plan_sha256'] + '  plan.json\n')
    (new_bundle / reference['output_relative']).mkdir(parents=True)
    replay_out = out / 'replays'; replay_out.mkdir()
    (out / 'references').mkdir()
    for unit, info in e['original_builds'].items():
        rp = original / old['output_relative'] / 'builds' / unit / 'build_record.json'
        for source in [rp, original / info['elf_path']]:
            target = replay_out / source.relative_to(original / old['output_relative'])
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
            copied_elves[target] = sha(source); assert sha(target) == sha(source)
    for rel, digest in e['reference_source_sha256'].items():
        target = out / 'new_sources' / rel; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, target); assert sha(target) == digest
    task_script = repo / 'harness/tacc_counter_verification/task.sh'

    def launch(phase, mode, ids):
        folder = out / 'launcher' / phase; folder.mkdir(parents=True)
        jobfile = folder / 'jobfile'
        with jobfile.open('x') as f:
            for index in ids: f.write(shlex.join(['bash', str(task_script), mode, str(index)]) + '\n')
        launch_env = dict(env, LAUNCHER_PPN='32', LAUNCHER_NHOSTS='1', LAUNCHER_LOCALHOST='1',
                          LAUNCHER_SCHED='interleaved', LAUNCHER_BIND='1', LAUNCHER_WORKDIR=str(folder),
                          LAUNCHER_JOB_FILE=str(jobfile), LAUNCHER_LOGFILE=str(folder / 'launcher.log'))
        for key in ['LAUNCHER_RMI', 'LAUNCHER_HOSTFILE', 'LAUNCHER_RMI_HOSTFILE']: launch_env.pop(key, None)
        phases_started.append(phase)
        code = subprocess.run([str(Path(env['LAUNCHER_DIR']) / 'paramrun')], cwd=folder, env=launch_env).returncode
        phase_exit_codes[phase] = code
        return code

    def reference_row(task):
        rid = f"{task['unit_id']}-{task['condition']}-{task['index']:03d}"
        rp = out / 'references/records' / (rid + '.json')
        pp = out / 'processes/reference' / f"{task['index']}.json"
        row = dict(index=task['index'], unit_id=task['unit_id'], frequency_hz=task['frequency_hz'],
                   phase=task['phase'], outcome='missing', cases=[], process_exit=None, record_sha256=None)
        if pp.exists(): row['process_exit'] = read(pp)['exit_code']
        if rp.exists():
            r = read(rp); assert all(r[k] == v for k, v in task.items())
            unit = next(u for u in reference['units'] if u['id'] == task['unit_id'])
            row.update(cases=r['cases'], record_sha256=sha(rp), error=r['error'])
            complete = (row['process_exit'] == 0 and r['outcome'] == 'complete' and r['application_completed']
                        and not r['error'] and not r['missing_cases'] and not r['duplicate_cases']
                        and Counter(c['case'] for c in r['cases']) == Counter(unit['expected_declared_cases']))
            if complete: row['outcome'] = 'complete'
        return row

    def replay_row(selected):
        task = selected['original_task']; rid = selected['primary_run_id']
        rp = out / 'replays/records' / (rid + '.json')
        pp = out / 'processes/replay' / f"{selected['diagnostic_index']}.json"
        row = dict(diagnostic_index=selected['diagnostic_index'], original_task_index=task['index'],
                   primary_record_path=selected['primary_record_path'], outcome='missing', agreement=False,
                   record_sha256=None, process_exit=read(pp)['exit_code'] if pp.exists() else None)
        if rp.exists():
            r = read(rp); assert all(r[k] == v for k, v in task.items())
            row.update(record_sha256=sha(rp), cases=r['cases'], error=r['error'])
            tr = read(out / 'replays/traces' / (rid + '.json'))
            normalized = hashlib.sha256(json.dumps({k:v for k,v in tr.items() if k != 'run_id'}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            complete = row['process_exit'] == 0 and r['outcome'] == 'complete' and r['application_completed'] and not r['error'] and not r['missing_cases'] and not r['duplicate_cases']
            agreement = (complete and r['cases'] == selected['expected_cases'] and
                         r['log_sha256']['uart'] == selected['expected_uart_sha256'] and
                         normalized == e['expected_normalized_traces'][str(selected['diagnostic_index'])])
            row.update(outcome='complete' if complete else 'missing', agreement=agreement,
                       uart_sha256=r['log_sha256']['uart'], normalized_trace_sha256=normalized)
        return row

    try:
        phases_started.append('build')
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda u: subprocess.run(['bash', str(task_script), 'build', u['id']], env=env).returncode, reference['units']))
        phase_exit_codes['build'] = results
        assert results == [0, 0], 'Diagnostic build failed; preserve evidence'
        for u in reference['units']:
            p = out / 'references/builds' / u['id'] / 'build_record.json'; b = read(p)
            assert b['status'] == 'built' and set(b['compiled_case_names']) == set(u['expected_declared_cases'])
            assert sha(out / 'references' / Path(b['elf_path']).relative_to(reference['output_relative'])) == b['elf_sha256']
        nominal = [t for t in reference['tasks'] if t['phase'] == 'qualification']
        launch('qualification', 'reference', [t['index'] for t in nominal])
        qualified = [reference_row(t) for t in nominal]
        save(out / 'qualification.json', dict(rows=qualified, all_passed=all(r['outcome'] == 'complete' and all(c['status']=='pass' for c in r['cases']) for r in qualified)))
        assert read(out / 'qualification.json')['all_passed'], 'Nominal reference qualification failed'
        launch('replays', 'replay', list(range(17)))
        replay_results = [replay_row(t) for t in e['selection']['replays']]
        save(out / 'replay_comparison.json', dict(rows=replay_results, all_agree=all(r['agreement'] for r in replay_results)))
        assert all(r['agreement'] for r in replay_results), 'Replay mismatch/missing; evaluation blocked'
        evaluation = [t for t in reference['tasks'] if t['phase'] == 'evaluation']
        launch('evaluation', 'reference', [t['index'] for t in evaluation])
    finally:
        guard()
        assert sha(image) == e['image_sha256']
        save(out / 'job_metadata/input_verification_after.json', dict(all_passed=True,
             active_counter_seals_unchanged=764, original_elves_unchanged=4, copied_original_bytes_unchanged=True,
             execution_code_unchanged=True, account=os.environ['SLURM_JOB_ACCOUNT']))
        refs = [reference_row(t) for t in reference['tasks']]
        replays = replay_results or [replay_row(t) for t in e['selection']['replays']]
        save(out / 'diagnostic_summary.json', dict(account=os.environ['SLURM_JOB_ACCOUNT'],
             phases_started=phases_started, phase_exit_codes=phase_exit_codes,
             reference_rows=refs, replay_rows=replays, original_records_replaced=False,
             planned_reference_processes=29, planned_replay_processes=17))

if __name__ == '__main__': main()
