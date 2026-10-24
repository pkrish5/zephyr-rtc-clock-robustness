#!/usr/bin/env python3
"""Seal existing forecast-only inputs without building or simulating anything."""
import argparse
import shutil
from pathlib import Path
from support import IMAGE_SHA, read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', required=True, type=Path)
    args = ap.parse_args()
    bundle = args.bundle.resolve()
    bundle.mkdir(parents=True, exist_ok=False)
    inputs = {}

    def copy(rel, expected=None):
        source, target = ROOT / rel, bundle / 'study' / rel
        digest = sha(source)
        if expected and digest != expected:
            raise RuntimeError('Frozen hash differs: ' + rel)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        if sha(target) != digest:
            raise RuntimeError('Copy differs')
        inputs['study/' + rel] = digest

    sample_rel = 'analysis/rtc_threshold_sample_v2/sample.json'
    forecast_rel = 'analysis/rtc_threshold_sample_v1/forecast.json'
    lock = read(ROOT / 'analysis/rtc_threshold_sample_v2/lock.json')
    copy(sample_rel, lock['sample_sha256'])
    copy(forecast_rel, lock['forecast_sha256'])
    for rel in ['analysis/rtc_threshold_sample_v2/lock.json', 'analysis/rtc_threshold_sample_v2/forecast_table.csv',
                'subjects/phase3_rtc/plan.json', 'results/rtc_timing_mutants_two_faults/manifest.json',
                'results/rtc_reference_triage/manifest.json']:
        copy(rel)
    roster = read(ROOT / sample_rel)['unsampled_prediction_only_run_ids']
    assert len(roster) == len(set(roster)) == 16
    forecasts = {p['run_id']: p for p in read(ROOT / forecast_rel)['predictions']}
    versions = read(ROOT / 'results/rtc_timing_mutants_two_faults/manifest.json')['versions']
    selected = {}
    for sid in sorted(roster):
        v = dict(versions[sid], role='prospective_forecast_only_validation')
        f = forecasts[sid]
        for kind in ('source', 'elf'):
            assert v[kind + '_sha256'] == f[kind + '_sha256']
            copy(v[kind + '_path'], v[kind + '_sha256'])
        v['predicted_failure_seeds'] = f['predicted_failure_seeds']
        selected[sid] = v
    refs = {}
    cases = {'rtc_alarm_callback': 'reference_rtc.test_alarm_callback',
             'rtc_alarm_pending': 'reference_rtc.test_alarm_pending',
             'rtc_time_counting': 'reference_rtc.test_calendar_counting'}
    for fam, b in read(ROOT / 'results/rtc_reference_triage/manifest.json')['reference_builds'].items():
        for rel, digest in b['input_sha256'].items():
            copy(rel, digest)
        copy(b['elf_path'], b['elf_sha256'])
        source = next(p for p in b['input_sha256'] if p.endswith('/test.c'))
        refs['reference-' + fam] = dict(kind='human', family=fam, model='reference', prompt_condition=None,
            role='failure_reference', source_path=source, source_sha256=sha(ROOT / source),
            elf_path=b['elf_path'], elf_sha256=b['elf_sha256'], selected_case=cases[fam])
    schedule = read(ROOT / 'subjects/phase3_rtc/plan.json')
    platforms = {}
    for hz in sorted(set(schedule['seeded_frequencies_hz']) | set(schedule['endpoints_hz'].values())):
        rel = f'results/phase3_rtc/platforms/stm32f4_rtc_lsi_{hz}.repl'
        copy(rel)
        platforms[str(hz)] = rel
    old_cache = ROOT / 'artifacts/tacc_phase1_20261023_v10/calibration-bundle/renode-cache'
    if not old_cache.exists():
        old_cache = ROOT / 'artifacts/tacc_phase1_20261023_v10/renode-cache'
    if not old_cache.exists():
        # Locate the sealed local Phase 1 transfer cache, never the user's home.
        matches = list((ROOT / 'artifacts/tacc_phase1_20261023_v10').glob('**/renode-cache'))
        if not matches:
            raise RuntimeError('Phase 1 transfer cache not found')
        old_cache = matches[0]
    shutil.copytree(old_cache, bundle / 'renode-cache')
    for p in (bundle / 'renode-cache').rglob('*'):
        if p.is_file():
            inputs[str(p.relative_to(bundle))] = sha(p)
    image = read(ROOT / 'artifacts/tacc_phase1_20261023_v10/returned-images/image.json')
    tasks = []
    for sid in sorted(selected):
        for cond, n in [('seeded', 100), ('min', 1), ('max', 1)]:
            for i in range(n):
                tasks.append(dict(index=len(tasks), suite_id=sid, condition=cond, seed=i))
    code = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'harness/tacc_phase2').rglob('*')
            if p.is_file() and p.suffix in ('.py', '.sh', '.sbatch')}
    frozen_code = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'harness').rglob('*.py')
                   if 'tacc_phase2' not in p.parts and '__pycache__' not in p.parts}
    output = 'results/tacc_phase2_ab_20261024_v1'
    (bundle / 'study' / output).mkdir(parents=True)
    plan = dict(registered_utc=utc(), phase='AB', tasks=tasks, versions=selected, references=refs,
                output_relative=output, platforms=platforms, image_sha256=IMAGE_SHA,
                execution_renode_version=image['actual_renode_version'], input_sha256=inputs,
                code_sha256=code, frozen_code_sha256=frozen_code, schedule_sha256=sha(ROOT / 'subjects/phase3_rtc/plan.json'),
                forecast_path=forecast_rel, sample_path=sample_rel,
                missing_policy='No retries; old 12 missing verdicts excluded from scope',
                replay_policy='Fresh process for each assertion failure; one reference per distinct failing task/frequency',
                endpoint_policy='Separate measured challenges, not claimed as frozen per-seed forecasts')
    save(bundle / 'plan.json', plan)
    (bundle / 'plan.sha256').write_text(sha(bundle / 'plan.json') + '  plan.json\n')
    print(sha(bundle / 'plan.json'), len(tasks))


if __name__ == '__main__':
    main()
