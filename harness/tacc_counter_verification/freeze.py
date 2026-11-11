#!/usr/bin/env python3
"""Freeze the diagnostic packet locally; this performs no build or simulation."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTE = ROOT / 'notes/counter_verification_2026-11-11_v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj):
    with p.open('x') as f: json.dump(obj, f, indent=2, sort_keys=True); f.write('\n')

def main():
    selection = json.loads((NOTE / 'selection.json').read_text())
    assert sha(NOTE / 'PROTOCOL.md') == selection['protocol_sha256']
    old_note = ROOT / 'notes/counter_repair_recovery_2026-11-05_v1'
    audit_plan = json.loads((old_note / 'audit_plan.json').read_text())
    original = old_note / 'verified-3558303-v1/output/evidence' / audit_plan['original_bundle_relative']
    old = json.loads((original / 'plan.json').read_text())
    assert sha(original / 'plan.json') == selection['original_counter_plan_sha256']
    app = ROOT / 'subjects/counter_verification_20261111_v1'
    source_hashes = {str(p.relative_to(app)):sha(p) for p in sorted(app.rglob('*')) if p.is_file()}
    assert len(source_hashes) == 7
    plan = copy.deepcopy(old)
    plan.update(phase='counter diagnostic references', registered_date='2026-11-11',
                account='CCR26073', production_authorized=False,
                output_relative='results/counter_verify_20261111_v1',
                compiler_parallelism=2, build_timeout_seconds=1800,
                reference_sources_sha256=source_hashes,
                frozen_s2_worker_sha256=sha(ROOT / 'harness/tacc_s2/worker.py'))
    base_unit = copy.deepcopy(next(u for u in old['units'] if u['variant'] == 'V0'))
    functional = dict(base_unit, id='f4-functional-reference', app='/reference-app/functional',
        max_virtual_seconds=700, wall_timeout_seconds=3000,
        expected_declared_cases=['ref_counter_verify.test_a_all_channels',
          'ref_counter_verify.test_b_short_relative_alarm','ref_counter_verify.test_c_single_shot_alarm_notop'])
    progress = dict(base_unit, id='f4-progress-control', app='/reference-app/progress',
        max_virtual_seconds=40, wall_timeout_seconds=900,
        expected_declared_cases=['ref_counter_progress.test_progress'])
    plan['units'] = [functional, progress]
    tasks = []
    for unit in plan['units']:
        for repeat in range(5):
            tasks.append(dict(index=len(tasks), unit_id=unit['id'], frequency_hz=32000,
                              condition='nominal', phase='qualification', repeat_index=repeat))
    for hz in selection['reference_legal_frequencies_hz']:
        tasks.append(dict(index=len(tasks), unit_id=functional['id'], frequency_hz=hz,
                          condition='legal_reference', phase='evaluation',
                          linked_primary_failures=[v for v in selection['reference_failure_slots'] if v['frequency_hz']==hz]))
    for hz, condition in [(10000,'slow_progress_control'),(64000,'fast_progress_control')]:
        tasks.append(dict(index=len(tasks), unit_id=progress['id'], frequency_hz=hz,
                          condition=condition, phase='evaluation'))
    plan['tasks'] = tasks
    assert len(tasks) == 29
    packet = NOTE / 'packet'; packet.mkdir(exist_ok=False)
    save(packet / 'reference_plan.json', plan)
    original_builds = {}
    for unit in old['units']:
        rp = original / old['output_relative'] / 'builds' / unit['id'] / 'build_record.json'
        b = json.loads(rp.read_text())
        assert sha(original / b['elf_path']) == b['elf_sha256']
        original_builds[unit['id']] = dict(elf_path=b['elf_path'], elf_sha256=b['elf_sha256'], build_record_sha256=sha(rp))
    normalized = {}
    for t in selection['replays']:
        rp = ROOT / t['primary_record_path']; r = json.loads(rp.read_text())
        assert sha(rp) == t['primary_record_sha256']
        assert r['elf_sha256'] == t['elf_sha256'] and r['cases'] == t['expected_cases']
        tr = rp.parent.parent / 'traces' / (r['run_id'] + '.json')
        assert sha(tr) == t['expected_trace_sha256']
        obj = json.loads(tr.read_text())
        normalized[str(t['diagnostic_index'])] = hashlib.sha256(json.dumps({k:v for k,v in obj.items() if k!='run_id'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    code = []
    for name in ['harness/tacc_counter_verification','harness/tacc_storage']:
        code += [p for p in sorted((ROOT / name).iterdir()) if p.is_file() and p.suffix in ['.py','.sh','.sbatch']]
    code += [ROOT/'harness/tacc_s2/worker.py', ROOT/'harness/tacc_s2_references/driver.py']
    e = dict(account='CCR26073', partition='development', maximum_workers=32,
        image_sha256=old['image_sha256'], image_relative='tacc_work/20261023-v10/images/rtc-ls6-v1.sif',
        original_bundle_relative=audit_plan['original_bundle_relative'],
        original_counter_plan_sha256=sha(original/'plan.json'), original_builds=original_builds,
        frozen_s2_worker_sha256=sha(ROOT/'harness/tacc_s2/worker.py'),
        active_counter_inputs_sha256=audit_plan['counter_inputs_sha256'],
        reference_source_sha256={str((app/p).relative_to(ROOT)):v for p,v in source_hashes.items()},
        code_sha256={str(p.relative_to(ROOT)):sha(p) for p in code},
        source_runtime_sha256=sha(ROOT/'harness/tacc_storage/runtime.sh'),
        source_run_packed_sha256=sha(ROOT/'harness/tacc_storage/run_packed.sh'),
        reference_plan_sha256=sha(packet/'reference_plan.json'), selection=selection,
        selection_sha256=sha(NOTE/'selection.json'), protocol_sha256=sha(NOTE/'PROTOCOL.md'),
        cost_sha256=sha(NOTE/'COST.json'), expected_normalized_traces=normalized,
        reservation_su_ceiling=2, normal_submission_authorized=False)
    save(packet/'execution.json', e)
    (packet/'execution.sha256').write_text(sha(packet/'execution.json')+'  execution.json\n')
    save(packet/'packet_receipt.json', dict(execution_sha256=sha(packet/'execution.json'),
        reference_plan_sha256=e['reference_plan_sha256'], new_reference_builds=2,
        qualification_launches=10, replay_launches=17, evaluation_launches=19,
        original_case_failure_slots_covered=87, original_inputs_modified=0,
        account='CCR26073', partition='development', nodes=1, wall_limit='02:00:00', ceiling_su=2))
    print((packet/'packet_receipt.json').read_text())

if __name__ == '__main__': main()
