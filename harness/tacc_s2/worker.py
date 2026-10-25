#!/usr/bin/env python3
"""Full-application S2 builds and per-setting launches in new output trees."""
import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path

IMAGE = '94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1'
CASE = re.compile(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]')
MARKERS = ('PROJECT EXECUTION SUCCESSFUL', 'PROJECT EXECUTION FAILED')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')


def verify(bundle):
    plan = json.loads((bundle / 'plan.json').read_text())
    if sha(bundle / 'plan.json') != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Plan seal differs')
    if plan['production_authorized'] or os.environ.get('SLURM_JOB_PARTITION') != 'development':
        raise RuntimeError('This worker is restricted to development qualification')
    if os.environ.get('RTC_CONTAINER_SHA256') != IMAGE:
        raise RuntimeError('Image hash differs')
    for rel, digest in plan['input_sha256'].items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Bundle input changed: ' + rel)
    return plan


def provenance(bundle):
    return dict(node_name=os.environ.get('RTC_NODE_NAME', socket.gethostname()),
        slurm_job_id=os.environ['SLURM_JOB_ID'], slurm_partition=os.environ['SLURM_JOB_PARTITION'],
        container_sha256=IMAGE, apptainer_version=os.environ['RTC_APPTAINER_VERSION'],
        apptainer_module='tacc-apptainer/1.4.1', launcher_module='launcher/3.10',
        plan_sha256=sha(bundle / 'plan.json'))


def build(bundle, plan, unit):
    z = Path('/opt/zephyrproject/zephyr')
    out = bundle / plan['output_relative'] / 'builds' / unit['id']
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, ZEPHYR_BASE=str(z), ZEPHYR_TOOLCHAIN_VARIANT='zephyr',
        ZEPHYR_SDK_INSTALL_DIR='/opt/zephyr-sdk-0.17.4', CCACHE_DISABLE='1',
        XDG_CACHE_HOME='/var/tmp', GIT_CONFIG_COUNT='4')
    modules = ['/opt/zephyrproject/modules/hal/' + x for x in ('cmsis', 'cmsis_6', 'stm32')]
    for i, path in enumerate([str(z)] + modules):
        env[f'GIT_CONFIG_KEY_{i}'] = 'safe.directory'
        env[f'GIT_CONFIG_VALUE_{i}'] = path
    actual = subprocess.check_output(['git', '-C', str(z), 'rev-parse', 'HEAD'], env=env, text=True).strip()
    if actual != plan['zephyr_commit']:
        raise RuntimeError('Upstream commit differs')
    for rel, digest in plan['upstream_input_sha256'].items():
        if sha(z / rel) != digest:
            raise RuntimeError('Upstream source differs: ' + rel)
    target = out / 'build'
    commands = [['cmake', '-S', str(z / unit['app']), '-B', str(target), '-G', 'Ninja',
        '-DBOARD=' + plan['boards'][unit['board_id']]['board'],
        '-DDTC_OVERLAY_FILE=' + str(bundle / unit['overlay']),
        '-DEXTRA_CONF_FILE=' + str(bundle / unit['config']),
        '-DZEPHYR_MODULES=' + ';'.join(modules),
        '-DPYTHON_EXECUTABLE=/opt/rtc-python/bin/python', '-DPython3_EXECUTABLE=/opt/rtc-python/bin/python'],
        ['cmake', '--build', str(target), '--parallel', str(plan['compiler_parallelism'])]]
    start, code, error = time.monotonic(), 0, None
    log = out / 'build.log'
    with log.open('x') as stream:
        for cmd in commands:
            try:
                code = subprocess.run(cmd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                    timeout=max(1, plan['build_timeout_seconds'] - (time.monotonic() - start))).returncode
            except subprocess.TimeoutExpired:
                code, error = 124, 'build timeout; infrastructure missingness, not test failure'
            if code:
                break
    elf = target / 'zephyr/zephyr.elf'
    products = {}
    for rel in ('zephyr/.config', 'zephyr/zephyr.dts', 'zephyr/include/generated/zephyr/devicetree_generated.h', 'CMakeCache.txt'):
        p = target / rel
        if p.exists():
            products[rel] = sha(p)
    record = dict(unit_id=unit['id'], board=plan['boards'][unit['board_id']]['board'],
        family=unit['family'], status='built' if code == 0 and elf.exists() else 'build_failure',
        exit_code=code, error=error, wall_seconds=round(time.monotonic() - start, 3),
        commands=commands, source_commit=actual, non_stock_rtc_only=unit['family'] in ('counter', 'seconds'),
        elf_path=str(elf.relative_to(bundle)) if elf.exists() else None,
        elf_sha256=sha(elf) if elf.exists() else None, build_products_sha256=products,
        config_sha256=sha(bundle / unit['config']), overlay_sha256=sha(bundle / unit['overlay']),
        log_sha256=sha(log), **provenance(bundle))
    if elf.exists():
        strings = subprocess.check_output(['strings', str(elf)], text=True, errors='replace').splitlines()
        symbols = set(strings)
        record['compiled_case_names'] = [c for c in unit['expected_declared_cases'] if c.split('.')[-1] in symbols or c in symbols]
    save(out / 'build_record.json', record)


def run(bundle, plan, task):
    unit = next(u for u in plan['units'] if u['id'] == task['unit_id'])
    board = plan['boards'][unit['board_id']]
    out = bundle / plan['output_relative']
    build_path = out / 'builds' / unit['id'] / 'build_record.json'
    build_record = json.loads(build_path.read_text())
    rid = f"{unit['id']}-{task['condition']}-{task['index']:03d}"
    record_path = out / 'records' / (rid + '.json')
    if build_record['status'] != 'built':
        save(record_path, dict(run_id=rid, **task, outcome='not_run_build_failure',
            cases=[], missing_cases=unit['expected_declared_cases'], **provenance(bundle)))
        return
    elf = bundle / build_record['elf_path']
    if sha(elf) != build_record['elf_sha256']:
        raise RuntimeError('Newly sealed build ELF changed')
    # Generic board adapter reuses the frozen monitor command/RunFor implementation.
    # Its F4-only GPIO startup probe is omitted on other boards; no old file changes.
    import sys
    sys.path.insert(0, '/opt/rtc-code/harness/phase0')
    from session import RenodeSession
    class BoardSession(RenodeSession):
        def read_gpio(self):
            return 0
    platform = out / 'platforms' / (rid + '.repl')
    platform.parent.mkdir(parents=True, exist_ok=True)
    rtc_source = f'using "/renode/platforms/boards/{board["platform"]}"\nrtc:\n    wakeupTimerFrequency: {task["frequency_hz"]}\n'
    if unit['board_id'] == 'f4':
        rtc_source += 'nvic:\n    systickFrequency: 16000000\n'
    if unit['family'] == 'wdt':
        rtc_source += ('watchdog' if unit['board_id'] == 'h753' else 'iwdg') + f':\n    frequency: {task["frequency_hz"]}\n'
    with platform.open('x') as f:
        f.write(rtc_source)
    logs = {}
    for kind in ('uart', 'monitor', 'traces'):
        d = out / kind
        d.mkdir(parents=True, exist_ok=True)
        logs[kind] = d / (rid + ('.json' if kind == 'traces' else '.log'))
        if logs[kind].exists():
            raise RuntimeError('Refusing to replace prior output')
    from datetime import datetime, timezone
    binary = Path(os.environ.get('RENODE_BIN', '/opt/renode/renode-pinned'))
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    if version != plan['renode_version']:
        raise RuntimeError('Calibrated Renode/runtime differs')
    started, virtual_ns, observations, registers = time.monotonic(), 0, [], []
    completed, error = False, None
    try:
        with BoardSession(binary, platform, elf, logs['monitor']) as s:
            s.command('cpu PerformanceInMips 16')
            s.command(f'sysbus.{board["uart"]} CreateFileBackend @{logs["uart"]} true')
            while virtual_ns < unit['max_virtual_seconds'] * 1000000000:
                if time.monotonic() - started > unit['wall_timeout_seconds'] - 60:
                    error = 'wall ceiling reached; missing verdicts retained'
                    break
                s.run_for_ns(plan['step_ns'])
                virtual_ns += plan['step_ns']
                text = logs['uart'].read_text(errors='replace') if logs['uart'].exists() else ''
                observations.append(dict(virtual_ns=virtual_ns, uart_bytes=len(text.encode()),
                    cases=[dict(case=c, status=status.lower()) for status, c in CASE.findall(text)],
                    suite_starts=text.count('Running TESTSUITE'), reset_waits=text.count('Waiting to restart MCU')))
                # Read only register evidence, with monitor bytes preserved, does not drive the test.
                if len(registers) < 1 or any(m in text for m in MARKERS):
                    r = dict(virtual_ns=virtual_ns)
                    for name, address in [('rtc_prer', board['rtc_address'] + 0x10),
                            ('dbg_idcode', 0x5C001000 if unit['board_id'] == 'h753' else 0xE0042000)]:
                        try:
                            r[name] = s.read_word(address)
                        except Exception as exc:
                            r[name + '_error'] = str(exc)
                    try:
                        r['systick_model_property'] = s.command('nvic SystickFrequency')
                    except Exception as exc:
                        r['systick_property_error'] = str(exc)
                    registers.append(r)
                if any(m in text for m in MARKERS):
                    completed = True
                    break
    except Exception as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    text = logs['uart'].read_text(errors='replace') if logs['uart'].exists() else ''
    case_rows = [dict(case=c, status=status.lower()) for status, c in CASE.findall(text)]
    counts = {c: [r['status'] for r in case_rows if r['case'] == c] for c in unit['expected_declared_cases']}
    missing = [c for c, statuses in counts.items() if not statuses]
    duplicate = [c for c, statuses in counts.items() if len(statuses) != 1 and statuses]
    wdt_ok = completed and any(r['status'] == 'pass' for r in case_rows) and text.count('Running TESTSUITE') > 1 and 'Testcase passed' in text
    outcome = 'harness_error' if error else 'complete' if completed else 'incomplete'
    trace = dict(run_id=rid, observations=observations, cases=case_rows, registers=registers,
                 application_completed=completed, outcome=outcome, error=error)
    save(logs['traces'], trace)
    register_dividers = []
    for r in registers:
        if 'rtc_prer' in r:
            value = r['rtc_prer']
            register_dividers.append(((value >> 16) & 0x7F) + 1)
            register_dividers[-1] *= (value & 0x7FFF) + 1
    record = dict(run_id=rid, **task, board=board['board'], family=unit['family'], outcome=outcome,
        timestamp_utc=datetime.now(timezone.utc).isoformat(), application_completed=completed,
        cases=case_rows, missing_cases=missing, duplicate_cases=duplicate,
        expected_declared_cases=unit['expected_declared_cases'], error=error,
        watchdog_reboot_and_completion=wdt_ok if unit['family'] == 'wdt' else None,
        suite_starts=text.count('Running TESTSUITE'), reset_waits=text.count('Waiting to restart MCU'),
        rtc_divider_observations=register_dividers, registers=registers,
        virtual_ns=virtual_ns, wall_seconds=round(time.monotonic() - started, 3),
        elf_sha256=sha(elf), build_record_sha256=sha(build_path), platform_sha256=sha(platform),
        renode_version=version, log_sha256={k: sha(p) if p.exists() else None for k, p in logs.items()},
        **provenance(bundle))
    save(record_path, record)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--stage', choices=['build', 'run'], required=True)
    ap.add_argument('--index', type=int, required=True)
    a = ap.parse_args()
    plan = verify(a.bundle)
    if a.stage == 'build':
        build(a.bundle, plan, plan['units'][a.index])
    else:
        run(a.bundle, plan, plan['tasks'][a.index])


if __name__ == '__main__':
    main()
