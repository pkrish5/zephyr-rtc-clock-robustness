#!/usr/bin/env python3
"""Compile disabled frozen drivers, then use the original quality simulator."""
import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path
from support import load_plan, original_module, provenance, save, sha, utc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--index', type=int, required=True)
    a = ap.parse_args()
    bundle = a.bundle.resolve()
    p = load_plan(bundle)
    study = bundle / 'study'
    out = study / p['output_relative']
    if (out / 'STOP.json').exists():
        raise RuntimeError('Integrity stop marker exists')
    t = p['tasks'][a.index]
    v = t['version']
    prov = dict(provenance(bundle), implementation=t['implementation'], task_index=a.index,
                model=v['model'], prompt_condition=v['prompt_condition'])
    save(out / 'claims' / f'{a.index:04d}.json', dict(task=t, **prov))
    try:
        for rel, digest in p['code_sha256'].items():
            if sha(Path('/phase2') / Path(rel).name) != digest:
                raise RuntimeError('Adapter differs: ' + rel)
        for rel, digest in p['frozen_code_sha256'].items():
            if sha(Path('/opt/rtc-code') / rel) != digest:
                raise RuntimeError('Original harness differs: ' + rel)
        files = list(v['sources']) + [v['conf'], p['platform']] + p['overlays'] + v.get('headers', [])
        if t['driver']:
            files.append(t['driver'])
        for rel in files:
            if sha(study / rel) != p['input_sha256']['study/' + rel]:
                raise RuntimeError('Input differs: ' + rel)
        zephyr = Path('/opt/zephyrproject/zephyr')
        env = dict(os.environ, ZEPHYR_BASE=str(zephyr), ZEPHYR_TOOLCHAIN_VARIANT='zephyr',
                   ZEPHYR_SDK_INSTALL_DIR='/opt/zephyr-sdk-0.17.4', CCACHE_DISABLE='1')
        safe = [str(zephyr), '/opt/zephyrproject/modules/hal/cmsis', '/opt/zephyrproject/modules/hal/cmsis_6',
                '/opt/zephyrproject/modules/hal/stm32']
        env['GIT_CONFIG_COUNT'] = str(len(safe))
        for i, path in enumerate(safe):
            env[f'GIT_CONFIG_KEY_{i}'] = 'safe.directory'
            env[f'GIT_CONFIG_VALUE_{i}'] = path
        commit = subprocess.check_output(['git', '-C', str(zephyr), 'rev-parse', 'HEAD'], env=env, text=True).strip()
        if commit != '3568e1b6d5cdd51a6b964a2a1d6d29200fea2056':
            raise RuntimeError('Pinned Zephyr commit differs')
        unit = out / 'builds' / f'{a.index:04d}'
        app, build = unit / 'app', unit / 'build'
        app.mkdir(parents=True, exist_ok=False)
        cmake = ('cmake_minimum_required(VERSION 3.20.0)\n'
                 'find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})\n'
                 'project(rtc_zero_control)\n'
                 'target_sources(app PRIVATE ' + ' '.join(str(study / rel) for rel in v['sources']) + ')\n')
        if v.get('app_define'):
            cmake += 'target_compile_definitions(app PRIVATE ' + v['app_define'] + ')\n'
        if t['driver']:
            cmake += ('get_target_property(rtc_sources drivers__rtc SOURCES)\n'
                      'list(FILTER rtc_sources EXCLUDE REGEX "rtc_ll_stm32[.]c$")\n'
                      'set_property(TARGET drivers__rtc PROPERTY SOURCES "${rtc_sources}")\n'
                      f'target_sources(drivers__rtc PRIVATE {study / t["driver"]})\n'
                      f'target_include_directories(drivers__rtc PRIVATE {zephyr}/drivers/rtc)\n'
                      'target_compile_definitions(drivers__rtc PRIVATE ' + ' '.join(t['macros']) + ')\n')
        (app / 'CMakeLists.txt').write_text(cmake)
        shutil.copyfile(study / v['conf'], app / 'prj.conf')
        commands = [[shutil.which('cmake'), '-S', str(app), '-B', str(build), '-G', 'Ninja',
             '-DBOARD=stm32f4_disco', '-DDTC_OVERLAY_FILE=' + ';'.join(str(study / rel) for rel in p['overlays']),
             '-DZEPHYR_MODULES=' + ';'.join(safe[1:]), '-DPYTHON_EXECUTABLE=/opt/rtc-python/bin/python',
             '-DPython3_EXECUTABLE=/opt/rtc-python/bin/python'],
            [shutil.which('cmake'), '--build', str(build), '--parallel', str(p['compiler_parallelism'])]]
        log = unit / 'build.log'
        started = time.monotonic()
        rc, error = 0, None
        with log.open('x') as f:
            for command in commands:
                try:
                    rc = subprocess.run(command, env=env, cwd=unit, stdout=f, stderr=subprocess.STDOUT,
                                        timeout=max(1, p['build_timeout_sec'] - (time.monotonic() - started))).returncode
                except subprocess.TimeoutExpired:
                    rc, error = 124, 'build_timeout'
                if rc:
                    break
        elf = build / 'zephyr/zephyr.elf'
        passed = rc == 0 and elf.is_file()
        build_record = dict(suite_id=t['suite_id'], family=v['family'], kind=v['kind'], commands=commands,
            timestamp_utc=utc(), status='pass' if passed else 'build_fail', returncode=rc, error=error,
            wall_seconds=round(time.monotonic() - started, 3), macros=t['macros'],
            source_inputs={rel: sha(study / rel) for rel in files},
            app_sha256={q.name: sha(q) for q in app.iterdir()}, log_path=str(log.relative_to(study)),
            log_sha256=sha(log), elf_path=str(elf.relative_to(study)) if passed else None,
            elf_sha256=sha(elf) if passed else None, zephyr_commit=commit, **prov)
        save(out / 'build_records' / f'{a.index:04d}.json', build_record)
        if not passed:
            print(build_record, flush=True)
            return
        mod = original_module('rtc_quality_run')
        mod.ROOT, mod.PLATFORM = study, study / p['platform']
        old_write = mod.write_new

        def writer(path, value):
            if path.parent.name == 'records':
                value = dict(value, **prov, build_record_sha256=sha(out / 'build_records' / f'{a.index:04d}.json'))
            old_write(path, value)
        mod.write_new = writer
        mod.simulate(out, f'{a.index:04d}-{t["implementation"]}-{t["suite_id"]}', t['suite_id'],
            v['family'], v['kind'], v.get('selected_case'), v['source_sha256'], elf,
            bundle / 'plan.json', max_virtual_sec=p['max_virtual_sec'])
    except Exception as exc:
        try:
            save(out / 'STOP.json', dict(reason=f'{type(exc).__name__}: {exc}', **prov))
        except FileExistsError:
            pass
        raise


if __name__ == '__main__':
    main()
