#!/usr/bin/env python3
"""Seal 207 primary and nine reference zero-fault build/run attempts."""
import argparse
import shutil
from pathlib import Path
from support import IMAGE_SHA, read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
LEAF = {'rtc_alarm_callback': 'callback', 'rtc_alarm_pending': 'pending', 'rtc_time_counting': 'counting'}
APPS = {'rtc_alarm_callback': 'subjects/phase1_lsi_rtc/selected_alarm_callback',
        'rtc_alarm_pending': 'subjects/rtc_alarm_pending/selected_case',
        'rtc_time_counting': 'subjects/rtc_counting/selected_case'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', required=True, type=Path)
    a = ap.parse_args()
    bundle = a.bundle.resolve()
    bundle.mkdir(parents=True, exist_ok=False)
    inputs = {}

    def copy(rel, expected=None):
        digest = sha(ROOT / rel)
        if expected and digest != expected:
            raise RuntimeError('Frozen input differs: ' + rel)
        dst = bundle / 'study' / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        inputs['study/' + rel] = digest
        return rel

    versions = read(ROOT / 'results/rtc_timing_mutants_two_faults/manifest.json')['versions']
    assert len(versions) == 69
    for sid, v in versions.items():
        copy(v['source_path'], v['source_sha256'])
        if v['kind'] == 'ai':
            v['sources'] = [v['source_path']]
            v['conf'] = copy(str(Path(v['source_path']).parent / 'prj.conf'))
        else:
            v['sources'] = [copy('subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/main.c'), v['source_path']]
            v['conf'] = copy(APPS[v['family']] + '/prj.conf')
            if v['family'] != 'rtc_time_counting':
                v['app_define'] = 'CONFIG_TEST_RTC_ALARM_TIME_MASK=7'
        # Original ELF hash remains provenance; D compiles a distinct new ELF.
    refs = {}
    cases = {'callback': 'test_alarm_callback', 'pending': 'test_alarm_pending', 'counting': 'test_calendar_counting'}
    for group in ('oscillator_zero', 'nonarrival_zero', 'alarm_offset_zero'):
        for family, leaf in LEAF.items():
            base = 'subjects/reference_rtc_alarm_offset' if group == 'alarm_offset_zero' else 'subjects/reference_rtc'
            source, conf = copy(f'{base}/{leaf}/test.c'), copy(f'{base}/{leaf}/prj.conf')
            header = copy(base + '/reference_common.h')
            refs[f'reference-{group}-{family}'] = dict(family=family, kind='reference', model='reference',
                prompt_condition=None, source_path=source, source_sha256=sha(ROOT / source),
                sources=[source], conf=conf, headers=[header], selected_case='reference_rtc.' + cases[leaf])
    overlays = [copy('subjects/phase1_zephyr/config/stm32f4_hsi.overlay'), copy('subjects/phase1_lsi_rtc/rtc_alias.overlay')]
    drivers = {g: copy('harness/rtc_driver_variants/' + f) for g, f in
               [('nonarrival_zero', 'rtc_ll_stm32_quality.c'), ('alarm_offset_zero', 'rtc_ll_stm32_alarm_offset.c')]}
    platform = copy('results/phase3_rtc/platforms/stm32f4_rtc_lsi_32000.repl')
    copy('results/rtc_timing_mutants_two_faults/manifest.json')
    copy('results/phase1/environment.json')
    macros = dict(oscillator_zero=[], alarm_offset_zero=['QUALITY_ALARM_OFFSET_SIGN=0'],
        nonarrival_zero=['QUALITY_DELAY_US=0', 'QUALITY_LATENCY_ALARM=0', 'QUALITY_LATENCY_COUNTING=0',
                        'QUALITY_NONARRIVAL_ALARM=0', 'QUALITY_NONARRIVAL_COUNTING=0'])
    tasks = []
    for group in macros:
        roster = {**versions, **{k: v for k, v in refs.items() if k.startswith('reference-' + group + '-') }}
        for sid, v in sorted(roster.items()):
            tasks.append(dict(index=len(tasks), suite_id=sid, implementation=group, version=v,
                              driver=drivers.get(group), macros=macros[group]))
    assert len(tasks) == 216
    shutil.copytree(ROOT / 'artifacts/tacc_phase1_20261023_v10/renode-cache', bundle / 'renode-cache')
    for p in (bundle / 'renode-cache').rglob('*'):
        if p.is_file():
            inputs[str(p.relative_to(bundle))] = sha(p)
    code = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'harness/tacc_phase2').rglob('*')
            if p.is_file() and p.suffix in ('.py', '.sh', '.sbatch')}
    frozen = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'harness').rglob('*.py')
              if 'tacc_phase2' not in p.parts and '__pycache__' not in p.parts}
    out = 'results/tacc_phase2_d_20261024_v1'
    (bundle / 'study' / out).mkdir(parents=True)
    image = read(ROOT / 'artifacts/tacc_phase1_20261023_v10/returned-images/image.json')
    save(bundle / 'plan.json', dict(registered_utc=utc(), phase='D', tasks=tasks, versions={**versions, **refs},
        overlays=overlays, platform=platform, output_relative=out, image_sha256=IMAGE_SHA,
        execution_renode_version=image['actual_renode_version'], renode_version=image['actual_renode_version'],
        input_sha256=inputs, code_sha256=code, frozen_code_sha256=frozen,
        policy='One build and one nominal run per successful build; no retries; references separate',
        max_virtual_sec=70, compiler_parallelism=2, build_timeout_sec=600))
    (bundle / 'plan.sha256').write_text(sha(bundle / 'plan.json') + '  plan.json\n')
    print(sha(bundle / 'plan.json'), len(tasks))


if __name__ == '__main__':
    main()
