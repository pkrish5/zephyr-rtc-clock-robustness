#!/usr/bin/env python3
"""Create an exclusive, sealed S2 qualification bundle. No firmware execution."""
import argparse
import csv
import hashlib
import json
import random
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Z = ROOT / 'subjects/upstream/zephyr'
IMAGE = '94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1'
BOARDS = {
    'f4': dict(board='stm32f4_disco', platform='stm32f4_discovery.repl', uart='usart2',
               minimum=17000, nominal=32000, maximum=47000, rtc_address=0x40002800,
               source='DS8626 Rev12; VDD3V; TA -40..105C'),
    'f767': dict(board='nucleo_f767zi', platform='nucleo_f767zi.repl', uart='usart3',
                 minimum=17000, nominal=32000, maximum=47000, rtc_address=0x40002800,
                 source='DS11532 Rev9; VDD3V; TA -40..105C'),
    'f746': dict(board='stm32f746g_disco', platform='stm32f7_discovery-bb.repl', uart='usart1',
                 minimum=17000, nominal=32000, maximum=47000, rtc_address=0x40002800,
                 source='DS10916 Rev5; VDD3V; TA -40..105C'),
    'h753': dict(board='nucleo_h753zi', platform='nucleo_h753zi.repl', uart='usart3',
                 minimum=29760, nominal=32000, maximum=33600, rtc_address=0x58004000,
                 source='DS12117 Rev10; revision V; VDD1.62..3.6V; TJ -40..105C'),
    'f072': dict(board='stm32f072b_disco', platform='stm32f072b_discovery.repl', uart='usart1',
                 minimum=30000, nominal=40000, maximum=50000, rtc_address=0x40002800,
                 source='DS9826 Rev6; VDDA3.3V; TA -40..105C; conditional divider qualification'),
}
APPS = dict(rtc='tests/drivers/rtc/rtc_api', counter='tests/drivers/counter/counter_basic_api',
            seconds='tests/drivers/counter/counter_seconds', wdt='tests/drivers/watchdog/wdt_basic_api')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--renode-root', type=Path, required=True)
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--runtime-inventory', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    configs = a.out / 'configs'
    configs.mkdir()
    inventory = json.loads(a.runtime_inventory.read_text())
    execution_version = inventory['renode_version']
    if execution_version != 'Renode v1.17.0\n  build: 1.17.0+20260907gitf1dd1b4af\n  build type: Release\n  runtime: .NET 8.0.21':
        raise RuntimeError('Expected the already calibrated Linux release/runtime pin')
    save(a.out / 'approved_runtime.json', dict(renode_version=execution_version,
        source_inventory_sha256=sha(a.runtime_inventory), image_sha256=IMAGE))
    confs = {
        'rtc': 'CONFIG_RTC_ALARM=y\nCONFIG_RTC_UPDATE=y\nCONFIG_RTC_CALIBRATION=y\nCONFIG_TEST_RTC_ALARM_TIME_MASK=7\n',
        'counter': 'CONFIG_RTC=n\nCONFIG_COUNTER_RTC_STM32=y\nCONFIG_COUNTER_RTC_STM32_SUBSECONDS=n\nCONFIG_COUNTER_TIMER_STM32=n\n',
        'seconds': 'CONFIG_RTC=n\nCONFIG_COUNTER_RTC_STM32=y\nCONFIG_COUNTER_RTC_STM32_SUBSECONDS=n\nCONFIG_COUNTER_TIMER_STM32=n\n',
        'wdt': 'CONFIG_WDT_DISABLE_AT_BOOT=y\n',
    }
    for family, s in confs.items():
        (configs / (family + '.conf')).write_text(s)
    cases = list(csv.DictReader((ROOT / 'analysis/subject_survey_20261025_v1/test_cases.csv').open()))
    units, original_platforms = [], {}
    for bid, board in BOARDS.items():
        # Explicit DTC_OVERLAY_FILE suppresses the application's stock board overlay.
        # Only F4 retains the historically frozen CPU overlay. Other CPU clocks stay stock.
        overlay = '/ { aliases { rtc = &rtc; rtc-0 = &rtc; }; };\n&clk_lsi { status = "okay"; };\n'
        if bid == 'f4':
            overlay += (ROOT / 'subjects/phase1_zephyr/config/stm32f4_hsi.overlay').read_text()
        if bid == 'f072':
            overlay += ('&rtc { clocks = <&rcc STM32_CLOCK(APB1, 28)>, '
                        '<&rcc STM32_SRC_LSI RTC_SEL(2)>; status = "okay"; };\n')
        else:
            overlay += '&rtc { status = "okay"; };\n'
        (configs / (bid + '.overlay')).write_text(overlay)
        watchdog_overlay = overlay + '\n&wwdg { status = "disabled"; };\n&iwdg { status = "okay"; };\n'
        if bid in ('f4', 'h753'):
            (configs / (bid + '-wdt.overlay')).write_text(watchdog_overlay)
        schedule = [random.Random(seed).randint(board['minimum'], board['maximum']) for seed in range(100)]
        old = json.loads((ROOT / 'subjects/phase3_rtc/plan.json').read_text())
        if bid == 'f4' and schedule != old['seeded_frequencies_hz']:
            raise RuntimeError('Original F4 seed schedule differs')
        board['seeded_frequencies_hz'] = schedule
        board['calibration_settings'] = [dict(condition='min', frequency_hz=board['minimum']),
            dict(condition='max', frequency_hz=board['maximum'])] + [
                dict(condition='seed', seed=i, frequency_hz=schedule[i]) for i in range(5)]
        for family, app in APPS.items():
            if family == 'wdt' and bid not in ('f4', 'h753'):
                continue
            expected = [r['case'] for r in cases if r['app'] == 'subjects/upstream/zephyr/' + app
                        and r['case_kind'] == 'ztest']
            units.append(dict(id=bid + '-' + family, board_id=bid, family=family, app=app,
                expected_declared_cases=expected, config='configs/' + family + '.conf',
                overlay='configs/' + bid + ('-wdt' if family == 'wdt' else '') + '.overlay',
                max_virtual_seconds={'rtc': 180, 'counter': 600, 'seconds': 30, 'wdt': 120}[family],
                wall_timeout_seconds={'rtc': 900, 'counter': 1800, 'seconds': 300, 'wdt': 600}[family]))
        seen = set()
        def copy_platform(p):
            p = p.resolve()
            if p in seen:
                return
            seen.add(p)
            rel = p.relative_to(a.renode_root.resolve())
            dest = a.out / 'renode' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            text = p.read_text()
            for inc in re.findall(r'using\s+"([^"]+)"', text):
                q = p.parent / inc if inc.startswith('.') else a.renode_root / inc
                copy_platform(q)
            # Keep relative ./ using paths; canonical platforms paths resolve via /renode bind.
            text = re.sub(r'using\s+"(platforms/[^\"]+)"', r'using "/renode/\1"', text)
            dest.write_text(text)
            original_platforms[str(rel)] = sha(p)
        copy_platform(a.renode_root / 'platforms/boards' / board['platform'])
    shutil.copytree(a.cache, a.out / 'renode-cache')
    tasks = []
    for unit in units:
        b = BOARDS[unit['board_id']]
        settings = [dict(condition='nominal', repeat_index=i, frequency_hz=b['nominal'])
                    for i in range(1 if unit['family'] == 'wdt' else 5)]
        if unit['family'] != 'wdt':
            settings += [dict(s, setting_index=i) for i, s in enumerate(b['calibration_settings'])]
        for s in settings:
            tasks.append(dict(index=len(tasks), unit_id=unit['id'], **s))
    probe = next(t['index'] for t in tasks if t['unit_id'] == 'f4-rtc' and t['condition'] == 'nominal' and t['index'] == 0)
    code = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'harness/tacc_s2').glob('*') if p.is_file()}
    inputs = {str(p.relative_to(a.out)): sha(p) for p in a.out.rglob('*') if p.is_file()}
    source_inputs = {}
    for app in APPS.values():
        for p in (Z / app).rglob('*'):
            if p.is_file():
                source_inputs[str(p.relative_to(Z))] = sha(p)
    for rel in ['drivers/rtc/rtc_ll_stm32.c', 'drivers/counter/counter_ll_stm32_rtc.c',
                'drivers/watchdog/wdt_iwdg_stm32.c', 'include/zephyr/drivers/clock_control/stm32_clock_control.h']:
        source_inputs[rel] = sha(Z / rel)
    plan = dict(schema=1, registered_date='2026-10-25', phase='S2 qualification only',
        zephyr_commit='3568e1b6d5cdd51a6b964a2a1d6d29200fea2056', image_sha256=IMAGE,
        output_relative='results/s2_qualification_20261025_v1', boards=BOARDS, units=units,
        tasks=tasks, probe_task_index=probe, maximum_workers=32, compiler_parallelism=2,
        input_sha256=inputs, code_sha256=code, upstream_input_sha256=source_inputs,
        original_platform_sha256=original_platforms, design_sha256=sha(ROOT / 'paper/DESIGN.md'),
        build_timeout_seconds=1800, step_ns=500000000, quantum_ns=1000,
        renode_version=execution_version, original_local_renode_version=old['renode_version'],
        production_authorized=False, watchdog_attempt=1,
        stop='Report qualification and recost; require approval before any normal job')
    save(a.out / 'plan.json', plan)
    (a.out / 'plan.sha256').write_text(sha(a.out / 'plan.json') + '  plan.json\n')
    print(json.dumps(dict(units=len(units), launches=len(tasks), plan_sha256=sha(a.out / 'plan.json'))))


if __name__ == '__main__':
    main()
