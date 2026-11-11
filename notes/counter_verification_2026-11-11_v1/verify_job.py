#!/usr/bin/env python3
"""Offline diagnostic audit. Never run simulations or replace primary records."""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXECUTION_SHA = '3380b6a28d9f4f160c1a1f4e0c11ef9a497e3be8ea40aeda29bfc2460bd03ae4'
read = lambda p: json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()


def save(p, obj):
    with p.open('x') as f: json.dump(obj, f, indent=2, sort_keys=True); f.write('\n')


def progress_band(delta, hz, elapsed_ms):
    """Protocol interval with its predeclared 2/22-ms observer tolerance."""
    lower = (delta - 1) * 32000 / hz * 1000 - 2
    upper = delta * 32000 / hz * 1000 + 22
    return dict(delta_ticks=delta, elapsed_ms=elapsed_ms, lower_ms=lower,
                upper_ms=upper, passed=delta >= 5 and lower <= elapsed_ms <= upper)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--returned', type=Path, required=True)
    p.add_argument('--job', required=True)
    p.add_argument('--sacct-json', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    state = read(a.sacct_json)
    assert state['job_id'] == a.job and state['state'] not in ['PENDING', 'RUNNING', 'COMPLETING']
    ep = HERE / 'packet/execution.json'; assert sha(ep) == EXECUTION_SHA
    e = read(ep); reference = read(HERE / 'packet/reference_plan.json')
    assert sha(HERE / 'packet/reference_plan.json') == e['reference_plan_sha256']
    stem = a.job + '-counter-diagnostics'
    receipt = read(a.returned / (stem + '.json'))
    archive = a.returned / (stem + '.tar.gz'); mp = a.returned / (stem + '.manifest.json.gz')
    assert receipt['slurm_job_id'] == a.job and receipt['output_state'] in ['complete', 'failed', 'interrupted']
    assert receipt['account'].upper() == 'CCR26073' and receipt['partition'] == 'development'
    assert receipt['container_sha256'] == e['image_sha256']
    assert sha(archive) == receipt['archive_sha256'] == (a.returned / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(mp) == receipt['manifest_sha256']
    manifest = json.loads(gzip.decompress(mp.read_bytes()))['files']
    assert len(manifest) == receipt['archive_entries']
    assert all(r['kind'] in ['file', 'directory'] for r in manifest.values())
    spec = importlib.util.spec_from_file_location('archive_audit', ROOT / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    helper.verify(archive, manifest)
    a.out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        for item in tar:
            rel = PurePosixPath(item.name)
            assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] == 'output'
            target = a.out / item.name
            if item.isdir(): target.mkdir(parents=True, exist_ok=True)
            else:
                assert item.isfile(); target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(item) as src, target.open('xb') as dst: shutil.copyfileobj(src, dst)
    out = a.out / 'output'; assert helper.inventory(out) == manifest
    baseline = read(ROOT / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    protected = []
    for phase in ['before', 'after']:
        proof = out / f'job_metadata/protected_{phase}.json'
        if proof.exists():
            v = read(proof)
            assert v['count'] == len(baseline) == 30067 and not v['changed']
            assert set(v['files']) == set(baseline)
            assert all(r['before_sha256'] == r['after_sha256'] == baseline[k] for k, r in v['files'].items())
            protected.append(phase)
    guards = []
    for phase in ['before', 'after']:
        proof = out / f'job_metadata/input_verification_{phase}.json'
        if proof.exists():
            v = read(proof); assert v['all_passed'] and v['account'].upper() == 'CCR26073'
            assert v['original_elves_unchanged'] == 4
            if phase == 'before':
                assert v['execution_sha256'] == EXECUTION_SHA and v['active_counter_seals'] == 764
                assert v['image_sha256'] == e['image_sha256']
            else:
                assert v['active_counter_seals_unchanged'] == 764 and v['execution_code_unchanged']
                assert v['copied_original_bytes_unchanged']
            guards.append(phase)
    for name, expected in [('execution.json', EXECUTION_SHA), ('reference_plan.json', e['reference_plan_sha256']),
                           ('selection.json', e['selection_sha256']), ('PROTOCOL.md', e['protocol_sha256']), ('COST.json', e['cost_sha256'])]:
        file = out / 'job_metadata' / name
        if file.exists(): assert sha(file) == expected
        elif receipt['output_state'] == 'complete': raise AssertionError('Complete archive missing sealed packet')
    for rel, digest in e['reference_source_sha256'].items():
        path = out / 'new_sources' / rel
        if path.exists(): assert sha(path) == digest
        elif receipt['output_state'] == 'complete': raise AssertionError('Missing diagnostic source')
    original = read(ROOT / 'notes/counter_repair_execution_2026-11-05_v1/plan.json')
    old_plan_path = ROOT / 'notes/counter_repair_recovery_2026-11-05_v1/verified-3558303-v1/output/evidence' / original['original_bundle_relative'] / 'plan.json'
    assert sha(old_plan_path) == e['original_counter_plan_sha256']; old = read(old_plan_path)
    builds, build_rows = {}, []
    for mode, plan in [('references', reference), ('replays', old)]:
        for unit in plan['units']:
            folder = out / mode / 'builds' / unit['id']; rp = folder / 'build_record.json'
            if not rp.exists(): continue
            b = read(rp); builds[(mode, unit['id'])] = b
            if mode == 'replays':
                assert sha(rp) == e['original_builds'][unit['id']]['build_record_sha256']
                assert b['elf_sha256'] == e['original_builds'][unit['id']]['elf_sha256']
            else:
                assert b['source_commit'] == plan['zephyr_commit'] and b['plan_sha256'] == e['reference_plan_sha256']
                assert b['config_sha256'] == plan['input_sha256'][unit['config']]
                assert b['overlay_sha256'] == plan['input_sha256'][unit['overlay']]
                assert sha(folder / 'build.log') == b['log_sha256']
                pp = out / 'processes/build' / (unit['id'] + '.json')
                process_exit = None
                if pp.exists():
                    v = read(pp)
                    assert v['slurm_job_id'] == a.job and v['account'].upper() == 'CCR26073'
                    assert v['mode'] == 'build' and v['selected'] == unit['id']
                    process_exit = v['exit_code']
                build_rows.append(dict(unit_id=unit['id'], status=b['status'], process_exit=process_exit,
                                       build_record_sha256=sha(rp), elf_sha256=b['elf_sha256']))
            if b['status'] == 'built':
                assert b['exit_code'] == 0 and set(b['compiled_case_names']) == set(unit['expected_declared_cases'])
                assert sha(out / mode / Path(b['elf_path']).relative_to(plan['output_relative'])) == b['elf_sha256']
                if mode == 'references':
                    retention = read(folder / 'retention.json')
                    assert retention['original_elves_changed'] is False and retention['intermediates_deleted'] is False
                    for rel, digest in retention['kept_sha256'].items():
                        assert sha(folder / 'build' / rel) == sha(folder / 'kept_products' / rel) == digest
    rows, cases, controls, agreements = [], [], [], []
    selected = {v['diagnostic_index']: v for v in e['selection']['replays']}
    expected = [('references', t['index'], t, reference) for t in reference['tasks']]
    expected += [('replays', i, t['original_task'], old) for i, t in selected.items()]
    for mode, process_mode in [('references', 'reference'), ('replays', 'replay')]:
        tasks = [(i, t) for m, i, t, _ in expected if m == mode]
        rids = {f"{t['unit_id']}-{t['condition']}-{t['index']:03d}" for _, t in tasks}
        assert {p.stem for p in (out / mode / 'records').glob('*.json')} <= rids
        assert {int(p.stem) for p in (out / 'processes' / process_mode).glob('*.json')} <= {i for i, _ in tasks}
    for mode, index, task, plan in expected:
        if mode == 'replays': assert task == old['tasks'][task['index']]
        unit = next(u for u in plan['units'] if u['id'] == task['unit_id'])
        rid = f"{unit['id']}-{task['condition']}-{task['index']:03d}"
        process_mode = 'reference' if mode == 'references' else 'replay'
        pp = out / 'processes' / process_mode / f'{index}.json'
        rp = out / mode / 'records' / (rid + '.json')
        row = dict(mode=mode, index=index, run_id=rid, frequency_hz=task['frequency_hz'],
                   phase=task.get('phase', 'replays'), outcome='missing', process_exit=None, record_sha256=None)
        if pp.exists():
            process = read(pp)
            assert process['slurm_job_id'] == a.job and process['account'].upper() == 'CCR26073'
            assert process['mode'] == process_mode and process['selected'] == str(index)
            row['process_exit'] = process['exit_code']
        complete = False
        if rp.exists():
            r = read(rp); assert r['run_id'] == rid and all(r[k] == v for k, v in task.items())
            assert r['slurm_job_id'] == a.job and r['slurm_partition'] == 'development'
            assert r['container_sha256'] == e['image_sha256'] and r['renode_version'] == plan['renode_version']
            assert r['plan_sha256'] == (e['reference_plan_sha256'] if mode == 'references' else e['original_counter_plan_sha256'])
            assert r['apptainer_module'] == 'tacc-apptainer/1.4.1' and r['launcher_module'] == 'launcher/3.10'
            b = builds[(mode, unit['id'])]
            assert r['elf_sha256'] == b['elf_sha256'] and r['build_record_sha256'] == sha(out / mode / 'builds' / unit['id'] / 'build_record.json')
            for kind, digest in r['log_sha256'].items():
                if digest: assert sha(out / mode / kind / (rid + ('.json' if kind == 'traces' else '.log'))) == digest
            platform = out / mode / 'platforms' / (rid + '.repl')
            assert sha(platform) == r['platform_sha256']
            assert platform.read_text() == f'using "/renode/platforms/boards/stm32f4_discovery.repl"\nrtc:\n    wakeupTimerFrequency: {task["frequency_hz"]}\nnvic:\n    systickFrequency: 16000000\n'
            trace = read(out / mode / 'traces' / (rid + '.json'))
            assert trace['cases'] == r['cases'] and trace['outcome'] == r['outcome'] and trace['error'] == r['error']
            text = (out / mode / 'uart' / (rid + '.log')).read_text(errors='replace')
            parsed = [dict(case=c, status=s.lower()) for s, c in re.findall(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]', text)]
            assert parsed == r['cases']
            complete = (row['process_exit'] == 0 and r['outcome'] == 'complete' and r['application_completed']
                        and not r['error'] and not r['missing_cases'] and not r['duplicate_cases']
                        and Counter(c['case'] for c in parsed) == Counter(unit['expected_declared_cases']))
            row.update(outcome='complete' if complete else 'missing', record_sha256=sha(rp), error=r['error'])
            cases.extend(dict(mode=mode, index=index, frequency_hz=task['frequency_hz'], phase=row['phase'],
                              usable=complete, **c) for c in parsed)
            if complete:
                monitor = (out / mode / 'monitor' / (rid + '.log')).read_text(errors='replace')
                assert 'cpu PerformanceInMips 16' in monitor and 'SetGlobalQuantum "0.000001"' in monitor
            if mode == 'replays':
                v = selected[index]
                assert sha(ROOT / v['primary_record_path']) == v['primary_record_sha256']
                norm = hashlib.sha256(json.dumps({k:v for k,v in trace.items() if k != 'run_id'}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                agree = complete and parsed == v['expected_cases'] and r['log_sha256']['uart'] == v['expected_uart_sha256'] and norm == e['expected_normalized_traces'][str(index)]
                agreements.append(dict(index=index, agreement=agree, primary_record_sha256=v['primary_record_sha256'],
                                       replay_record_sha256=sha(rp), uart_sha256=r['log_sha256']['uart'], normalized_trace_sha256=norm))
            elif unit['id'] == 'f4-progress-control':
                values = re.findall(r'VERIFY_RATE delta_ticks=(\d+) elapsed_ms=(\d+)', text)
                band = progress_band(int(values[0][0]), task['frequency_hz'], int(values[0][1])) if len(values) == 1 else dict(passed=False)
                controls.append(dict(index=index, frequency_hz=task['frequency_hz'], complete=complete, **band))
        rows.append(row)
    assert len(rows) == 46
    # Keep both the partial vectors and missing outcomes. No incomplete case is promoted to a verdict.
    for name, data in [('processes.csv', rows), ('case_verdicts.csv', cases)]:
        if data:
            keys = list(dict.fromkeys(k for row in data for k in row))
            with (a.out / name).open('x', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(data)
    qualification = [r for r in rows if r['phase'] == 'qualification']
    nominal_pass = (len(qualification) == 10 and all(r['outcome'] == 'complete' for r in qualification)
                    and all(c['status'] == 'pass' for c in cases if c['phase'] == 'qualification'))
    replay_pass = len(agreements) == 17 and all(r['agreement'] for r in agreements)
    input_guarded = protected == ['before', 'after'] and guards == ['before', 'after']
    complete_job = receipt['output_state'] == 'complete' and state['state'] == 'COMPLETED' and state['exit_code'] == '0:0'
    if receipt['output_state'] == 'complete':
        assert input_guarded and nominal_pass and replay_pass
        assert len(build_rows) == 2 and all(r['status'] == 'built' and r['process_exit'] == 0 for r in build_rows)
    coverage = []
    name_map = {'counter_basic.test_all_channels': 'ref_counter_verify.test_a_all_channels',
                'counter_basic.test_short_relative_alarm': 'ref_counter_verify.test_b_short_relative_alarm',
                'counter_basic.test_single_shot_alarm_notop': 'ref_counter_verify.test_c_single_shot_alarm_notop'}
    for slot in e['selection']['reference_failure_slots']:
        # Coverage links are descriptive; a clean-state reference is not phase equivalent.
        case_name = slot.get('case', slot.get('case_name'))
        primary_path = ROOT / slot['primary_record_path']
        assert sha(primary_path) == slot['primary_record_sha256']
        primary = read(primary_path)
        assert primary['frequency_hz'] == slot['frequency_hz']
        assert {'case': case_name, 'status': 'fail'} in primary['cases']
        matching = [c for c in cases if c['mode'] == 'references' and c['phase'] == 'evaluation'
                    and c['frequency_hz'] == slot['frequency_hz'] and c['case'] == name_map[case_name]]
        assert len(matching) <= 1
        outcome = matching[0]['status'] if matching and matching[0]['usable'] else 'missing'
        coverage.append(dict(primary_slot=slot, reference_case=name_map[case_name], reference_outcome=outcome,
                             phase_equivalent=False))
    assert len(coverage) == 87
    save(a.out / 'reference_coverage.json', coverage)
    by_cell = []
    for task in reference['tasks']:
        found = [c for c in cases if c['mode'] == 'references' and c['index'] == task['index'] and c['usable']]
        unit = next(u for u in reference['units'] if u['id'] == task['unit_id'])
        counts = {k: sum(c['status'] == k for c in found) for k in ['pass', 'fail', 'skip']}
        counts['missing'] = len(unit['expected_declared_cases']) - len(found)
        by_cell.append(dict(index=task['index'], unit_id=unit['id'], frequency_hz=task['frequency_hz'],
                            phase=task['phase'], counts=counts))
    result = dict(job_id=a.job, output_state=receipt['output_state'], sacct=state,
                  archive_sha256=sha(archive), exact_archive_entries=len(manifest), extracted_inventory_matches=True,
                  protected_before_after_verified=protected, input_guards_verified=guards,
                  qualification_passed=nominal_pass, replays_agree=replay_pass, complete_job=complete_job,
                  planned_processes=46, complete_processes=sum(r['outcome'] == 'complete' for r in rows),
                  missing_processes=sum(r['outcome'] == 'missing' for r in rows),
                  explicit_usable_case_counts=dict(Counter(c['status'] for c in cases if c['usable'])),
                  partial_case_counts=dict(Counter(c['status'] for c in cases if not c['usable'])),
                  reference_cell_counts=by_cell,
                  residual_primary_coverage_counts=dict(Counter(c['reference_outcome'] for c in coverage)),
                  activation_controls=controls, replay_comparisons=agreements,
                  build_outcomes=build_rows,
                  original_records_replaced=False, scientific_interpretation_requires_review=True)
    save(a.out / 'verification.json', result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__': main()
