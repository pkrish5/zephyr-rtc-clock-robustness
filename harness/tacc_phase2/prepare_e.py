#!/usr/bin/env python3
"""Seal the approved five-version, 33-subject repair study; no builds/runs."""
import argparse
import shutil
from pathlib import Path
from support import IMAGE_SHA, read, save, sha, utc
from prepare_d import APPS, LEAF

ROOT = Path(__file__).resolve().parents[2]


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
            raise RuntimeError('Source/input differs: ' + rel)
        dst = bundle / 'study' / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        inputs['study/' + rel] = digest
        return rel

    cohort = 'notes/repair_execution_20261024_v2/variants.json'
    copy(cohort)
    for rel in ['notes/repair_execution_20261024_v2/patch_sites.json', 'notes/repair_revision_2026-10-24/amendment.md',
                'notes/repair_revision_2026-10-24/amendment.sha256', 'notes/repair_review_2026-10-24/subjects.json']:
        copy(rel)
    versions = {}
    for vid, row in read(ROOT / cohort)['versions'].items():
        copy(row['source_path'], row['source_sha256'])
        copy(row['elf_path'], row['elf_sha256'])
        source = copy(row['variant_source_path'], row['variant_source_sha256'])
        for rel, digest in row['support_inputs'].items():
            copy(rel, digest)
        conf = str(Path(row['source_path']).parent / 'prj.conf') if row['kind'] == 'ai' else APPS[row['family']] + '/prj.conf'
        sources = [source]
        if row['kind'] == 'human':
            sources.insert(0, copy('subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/main.c'))
        v = dict(row, source_path=source, source_sha256=row['variant_source_sha256'], sources=sources,
                 conf=copy(conf), role='exploratory_mechanical_repair',
                 original_source_path=row['source_path'], original_source_sha256=row['source_sha256'],
                 original_elf_path=row['elf_path'], original_elf_sha256=row['elf_sha256'],
                 reuse_nominal_elf=row['variant'] == 'V0' or row['unchanged_from_v0'])
        if row['kind'] == 'human' and row['family'] != 'rtc_time_counting':
            v['app_define'] = 'CONFIG_TEST_RTC_ALARM_TIME_MASK=7'
        versions[vid] = v
    references = {}
    cases = {'callback': 'test_alarm_callback', 'pending': 'test_alarm_pending', 'counting': 'test_calendar_counting'}
    for family, leaf in LEAF.items():
        base = 'subjects/reference_rtc'
        source = copy(f'{base}/{leaf}/test.c')
        copy(base + '/reference_common.h')
        offset_base = 'subjects/reference_rtc_alarm_offset'
        offset_source = copy(f'{offset_base}/{leaf}/test.c')
        copy(offset_base + '/reference_common.h')
        references['reference-' + family] = dict(kind='human', family=family, model='reference', prompt_condition=None,
            role='repair_reference', variant='reference', source_path=source, source_sha256=sha(ROOT / source),
            sources=[source], conf=copy(f'{base}/{leaf}/prj.conf'), selected_case='reference_rtc.' + cases[leaf],
            offset_sources=[offset_source], offset_source_sha256=sha(ROOT / offset_source),
            offset_conf=copy(f'{offset_base}/{leaf}/prj.conf'), reuse_nominal_elf=False)
    overlays = [copy('subjects/phase1_zephyr/config/stm32f4_hsi.overlay'), copy('subjects/phase1_lsi_rtc/rtc_alias.overlay')]
    drivers = {k: copy('harness/rtc_driver_variants/' + fn) for k, fn in
               [('nonarrival', 'rtc_ll_stm32_quality.c'), ('offset', 'rtc_ll_stm32_alarm_offset.c')]}
    copy('subjects/phase3_rtc/plan.json')
    schedule = read(ROOT / 'subjects/phase3_rtc/plan.json')
    platforms = {}
    for hz in sorted(set(schedule['seeded_frequencies_hz']) | set(schedule['endpoints_hz'].values()) | {32000}):
        platforms[str(hz)] = copy(f'results/phase3_rtc/platforms/stm32f4_rtc_lsi_{hz}.repl')
    for v in read(ROOT / 'results/rtc_timing_mutants_two_faults/manifest.json')['platforms'].values():
        platforms[str(v['effective_rtc_hz'])] = copy(v['path'], v['sha256'])
    shutil.copytree(ROOT / 'artifacts/tacc_phase1_20261023_v10/renode-cache', bundle / 'renode-cache')
    for f in (bundle / 'renode-cache').rglob('*'):
        if f.is_file():
            inputs[str(f.relative_to(bundle))] = sha(f)
    code = {str(f.relative_to(ROOT)): sha(f) for f in (ROOT / 'harness/tacc_phase2').rglob('*')
            if f.is_file() and f.suffix in ('.py', '.sh', '.sbatch')}
    frozen = {str(f.relative_to(ROOT)): sha(f) for f in (ROOT / 'harness').rglob('*.py')
              if 'tacc_phase2' not in f.parts and '__pycache__' not in f.parts}
    out = 'results/tacc_phase2_e_20261024_v1'
    (bundle / 'study' / out).mkdir(parents=True)
    image = read(ROOT / 'artifacts/tacc_phase1_20261023_v10/returned-images/image.json')
    all_versions = {**versions, **references}
    tasks = [dict(index=i, version_id=vid) for i, vid in enumerate(sorted(all_versions))]
    save(bundle / 'plan.json', dict(registered_utc=utc(), phase='E', tasks=tasks, versions=versions, references=references,
        output_relative=out, platforms=platforms, overlays=overlays, drivers=drivers, image_sha256=IMAGE_SHA,
        input_sha256=inputs, code_sha256=code, frozen_code_sha256=frozen,
        renode_version=image['actual_renode_version'], execution_renode_version=image['actual_renode_version'],
        schedule_sha256=sha(ROOT / 'subjects/phase3_rtc/plan.json'), compiler_parallelism=2, build_timeout_sec=600,
        nominal_repeats=5, gate_max_virtual_sec=70, legal_max_virtual_sec=60, fault_max_virtual_sec=70,
        counting_offset_controls='omitted as optional; counting never enters alarm-offset denominator',
        missing_policy='No retries. Gate losses and missing evaluations remain separate failed/unconfirmed attempts.',
        phase3_policy='STOP with before/after counts before paper edits; E2 remains on hold'))
    (bundle / 'plan.sha256').write_text(sha(bundle / 'plan.json') + '  plan.json\n')
    print(sha(bundle / 'plan.json'), len(tasks), 'gate units; 165 primary versions + three references')


if __name__ == '__main__':
    main()
